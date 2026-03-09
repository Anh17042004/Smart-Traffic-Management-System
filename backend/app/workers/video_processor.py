"""
workers/video_processor.py
Refactored từ AnalyzeOnRoadForMultiProcessing.py → VideoProcessorPool

Thay đổi:
  - Đổi tên class cho rõ ràng hơn
  - Import từ app.* thay vì import cũ
  - Thêm method get_names() để lấy danh sách tên đường
  - Dùng road_config từ app.core.config (thay vì settings_metric_transport cũ)
"""
import os
import sys
import atexit
import signal
from multiprocessing import Process, Manager, freeze_support

from app.core.config import road_config
from app.utils.transport_utils import convert_frame_to_byte, log

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class VideoProcessorPool:
    """Quản lý multiprocessing pool xử lý nhiều video song song.

    Mỗi video chạy trong 1 process riêng biệt (tránh GIL).
    Chia sẻ dữ liệu qua Manager.dict() (shared memory).

    Attributes:
        shared_data: Dict chia sẻ giữa các process {road_name: {info, frame}}
        names: Danh sách tên tuyến đường đang xử lý
        processes: List các Process đang chạy
    """

    def __init__(
        self,
        regions=None,
        path_videos=None,
        meter_per_pixels=None,
        show_log: bool = False,
        show: bool = False,
        is_join_processes: bool = False,
    ):
        """
        Args:
            regions: List polygon regions cho từng tuyến đường
            path_videos: List đường dẫn video
            meter_per_pixels: List tỉ lệ mét/pixel
            show_log: In log ra console (dùng khi dev)
            show: Hiển thị video qua cv2 (luôn False khi chạy server)
            is_join_processes: Join processes (False khi tích hợp API để không block event loop)
        """
        self.regions = regions or road_config.REGIONS
        self.path_videos = path_videos or road_config.PATH_VIDEOS
        self.meter_per_pixels = meter_per_pixels or road_config.METER_PER_PIXELS

        self.manager = Manager()
        self.shared_data = self.manager.dict()
        self.show_log = show_log
        self.show = show
        self.processes = []
        self.names = []
        self.is_join_processes = is_join_processes

        # Cleanup khi nhận signal Ctrl+C hoặc SIGTERM
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self.cleanup_processes)

    def _signal_handler(self, signum, frame):
        """Xử lý signal để tắt gracefully."""
        print(f"\nNhận signal {signum}, đang dừng các process...")
        self.cleanup_processes()
        sys.exit(0)

    def cleanup_processes(self):
        """Terminate tất cả child processes một cách an toàn."""
        if not hasattr(self, "processes"):
            return
        for p in self.processes:
            if p.is_alive():
                print(f"Terminate process {p.pid}...")
                p.terminate()
                p.join(timeout=5)
                if p.is_alive():
                    print(f"Force kill process {p.pid}...")
                    p.kill()
        print("Tất cả processes đã dừng.")

    @staticmethod
    def _run_analyzer(region, path_video, meter_per_pixel, info_dict, frame_dict, show):
        """Hàm target chạy trong child process.

        Phải là @staticmethod để tránh pickle self (YOLO không thể pickle được).
        Tất cả objects YOLO được khởi tạo TRONG process con này.
        """
        try:
            # Import trong process con (tránh pickle)
            from app.ai.detector import RoadDetector
            analyzer = RoadDetector(
                path_video=path_video,
                meter_per_pixel=meter_per_pixel,
                info_dict=info_dict,
                frame_dict=frame_dict,
                region=region,
                show=show,
            )
            analyzer.process_on_single_video()
        except Exception as e:
            print(f"Lỗi khi xử lý {path_video}: {e}")

    def run_multiprocessing(self):
        """Khởi động tất cả processes — gọi 1 lần duy nhất trong lifespan startup."""
        freeze_support()

        for path_video, meter_per_pixel, region in zip(
            self.path_videos, self.meter_per_pixels, self.regions
        ):
            name = path_video.split("/")[-1][:-4]
            self.names.append(name)

            # Tạo shared dicts cho từng tuyến đường
            info_dict = self.manager.dict({
                "count_car": 0,
                "count_motor": 0,
                "speed_car": 0,
                "speed_motor": 0,
            })
            frame_dict = self.manager.dict({"frame": ""})

            self.shared_data[name] = {
                "info": info_dict,
                "frame": frame_dict,
            }

            p = Process(
                target=self._run_analyzer,
                args=(region, path_video, meter_per_pixel, info_dict, frame_dict, self.show),
            )
            self.processes.append(p)

        # Start tất cả processes
        for p in self.processes:
            p.start()

        if self.show_log:
            Process(target=log, args=(self.names, self.shared_data)).start()

        if self.is_join_processes:
            self._join_all()

    def _join_all(self):
        """Join tất cả processes với timeout."""
        for p in self.processes:
            if p.is_alive():
                p.join(timeout=10)
                if p.is_alive():
                    p.terminate()
                    p.join(timeout=2)
                    if p.is_alive():
                        p.kill()
        print("All processes stopped.")

    # ─────────────────────────────────────────────
    # Public API — được gọi bởi api/v1/traffic.py
    # ─────────────────────────────────────────────

    def get_names(self) -> list[str]:
        """Trả về danh sách tên tuyến đường đang được giám sát."""
        return self.names

    def get_frame_road(self, road_name: str) -> bytes:
        """Lấy JPEG frame hiện tại của tuyến đường.

        Args:
            road_name: Tên tuyến đường (ví dụ: "Đường Láng")

        Returns:
            bytes: JPEG image bytes, hoặc b"" nếu không tìm thấy
        """
        if road_name not in self.names:
            return b""
        raw = self.shared_data[road_name]["frame"].get("frame", b"")
        return raw if isinstance(raw, bytes) else b""

    def get_info_road(self, road_name: str) -> dict:
        """Lấy thông tin phương tiện hiện tại của tuyến đường.

        Args:
            road_name: Tên tuyến đường

        Returns:
            dict: {count_car, count_motor, speed_car, speed_motor}
        """
        if road_name not in self.names:
            return {}
        return dict(self.shared_data[road_name]["info"])
