"""
ai/detector.py
Refactored từ:
  - AnalyzeOnRoadBase.py  → RoadDetectorBase (abstract)
  - AnalyzeOnRoad.py      → RoadDetector (concrete, dùng với multiprocessing)

Thay đổi so với code cũ:
  - Import từ app.core.config và app.utils.transport_utils (thay vì import cũ)
  - Đổi tên class cho rõ ràng hơn
"""
import os
from abc import abstractmethod
from datetime import datetime

import cv2
import cvzone
import numpy as np
from overrides import override
from ultralytics import solutions

from app.core.config import settings, road_config
from app.utils.transport_utils import avg_none_zero_batch, convert_frame_to_byte

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class RoadDetectorBase:
    """Base class xử lý video tuần tự — YOLO + ByteTrack + SpeedEstimator.

    Attributes:
        count_car_display (int): Số xe ô tô trung bình trong time_step
        count_motor_display (int): Số xe máy trung bình trong time_step
        speed_car_display (int): Tốc độ trung bình ô tô (km/h)
        speed_motor_display (int): Tốc độ trung bình xe máy (km/h)
        frame_output (np.ndarray): Frame đã được vẽ thông tin lên
    """

    def __init__(
        self,
        path_video: str = "./video_test/Đường Láng.mp4",
        meter_per_pixel: float = 0.06,
        model_path: str = None,
        time_step: int = 30,
        is_draw: bool = True,
        device: str = None,
        iou: float = 0.3,
        conf: float = 0.2,
        show: bool = False,
        region: np.ndarray = np.array([[50, 400], [50, 265], [370, 130], [600, 130], [600, 400]]),
    ):
        model_path = model_path or settings.MODELS_PATH
        device = device or settings.DEVICE

        self.speed_tool = solutions.SpeedEstimator(
            model=model_path,
            tracker="bytetrack.yaml",
            verbose=False,
            show=False,
            device=device,
            iou=iou,
            conf=conf,
            meter_per_pixel=meter_per_pixel,
            max_hist=20,
            fps=20
         
        )

        self.region = region
        self.region_pts = region.reshape((-1, 1, 2))
        self.region_bbox = cv2.boundingRect(self.region_pts)

        self.show = show
        self.path_video = path_video
        self.name = path_video.split("/")[-1][:-4]

        self.count_car_display = 0
        self.list_count_car = []
        self.speed_car_display = 0
        self.list_speed_car = []

        self.count_motor_display = 0
        self.list_count_motor = []
        self.speed_motor_display = 0
        self.list_speed_motor = []

        self.time_pre = datetime.now()
        self.frame_output = None
        self.time_step = time_step
        self.frame_predict = None
        self.is_draw = is_draw
        self.delta_time = 0
        self.time_pre_for_fps = datetime.now()

        # ROI offset
        self.roi_y_start = 130
        self.roi_x_start = 50

        # Draw params
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.font_thickness = 1
        self.color_motor = (0, 0, 255)
        self.color_car = (255, 0, 0)
        self.color_region = (0, 255, 255)

        # Frame size chuẩn cho model predict
        self.target_size = road_config.TARGET_SIZE # (width, height) cho cv2.resize

        # Tracking state
        self.ids = None
        self.speeds = {}
        self.boxes = None
        self.classes = None
        self.ids_old = set()

    @abstractmethod
    def update_for_frame(self):
        """Ghi frame output vào shared memory."""
        pass

    @abstractmethod
    def update_for_vehicle(self):
        """Ghi thông tin phương tiện vào shared memory."""
        pass

    def update_data(self):
        """Cập nhật shared data sau mỗi frame và mỗi time_step."""
        self.update_for_frame()

        time_now = datetime.now()
        self.delta_time = (time_now - self.time_pre).total_seconds()

        if self.delta_time >= self.time_step:
            self.time_pre = time_now
            (
                self.count_car_display,
                self.speed_car_display,
                self.count_motor_display,
                self.speed_motor_display,
            ) = avg_none_zero_batch(
                self.list_count_car,
                self.list_speed_car,
                self.list_count_motor,
                self.list_speed_motor,
            )
            self.update_for_vehicle()
            self.list_count_car.clear()
            self.list_count_motor.clear()
            self.list_speed_car.clear()
            self.list_speed_motor.clear()
            self.ids_old.clear()

    def process_single_frame(self, frame_input: np.ndarray):
        """Xử lý 1 frame: resize chuẩn → YOLO inference → post-processing → draw."""
        try:
            self.frame_output = cv2.resize(frame_input, self.target_size)
            self.frame_predict = self.frame_output[self.roi_y_start:, self.roi_x_start:]
            self.speed_tool.process(self.frame_predict.copy())
            self.post_processing()
            if self.is_draw:
                self.draw_info_to_frame_output()
            self.update_data()
        except Exception as e:
            print(f"Lỗi khi xử lý frame {self.name}: {e}")

    def post_processing(self):
        """Extract tracking results và tính toán tốc độ, mật độ."""
        if self.speed_tool.track_data is None:
            return

        track_data = self.speed_tool.track_data
        speeds_dict = self.speed_tool.spd

        if track_data.id is None:
            return

        ids = track_data.id.cpu().numpy().astype(np.int32)
        classes = track_data.cls.cpu().numpy().astype(np.int32)
        boxes = track_data.xyxy.cpu().numpy().astype(np.int32)

        self.speeds = speeds_dict
        self.ids = ids
        self.classes = classes
        self.boxes = boxes

        car_mask = classes == 0
        motor_mask = classes == 1
        self.list_count_car.append(int(np.sum(car_mask)))
        self.list_count_motor.append(int(np.sum(motor_mask)))

        car_ids = ids[car_mask]
        motor_ids = ids[motor_mask]
        ids_old = self.ids_old

        def collect_speeds(new_ids: np.ndarray):
            if new_ids.size == 0:
                return []
            if ids_old:
                mask_new = ~np.isin(new_ids, list(ids_old), assume_unique=False)
                new_ids = new_ids[mask_new]
            if new_ids.size == 0:
                return []
            spd_arr = np.array([speeds_dict.get(int(i), 0.0) for i in new_ids], dtype=np.float32)
            valid_mask = spd_arr > 0.0
            if not np.any(valid_mask):
                return []
            ids_old.update(new_ids[valid_mask].tolist())
            return spd_arr[valid_mask].tolist()

        car_speeds = collect_speeds(car_ids)
        motor_speeds = collect_speeds(motor_ids)
        if car_speeds:
            self.list_speed_car.extend(car_speeds)
        if motor_speeds:
            self.list_speed_motor.extend(motor_speeds)

    def draw_info_to_frame_output(self):
        """Vẽ bounding box, tốc độ và vùng ROI lên frame."""
        try:
            if self.ids is not None and len(self.ids) > 0:
                x1 = self.boxes[:, 0]
                y1 = self.boxes[:, 1]
                x2 = self.boxes[:, 2]
                y2 = self.boxes[:, 3]
                cx = ((x1 + x2) // 2).astype(np.int32)
                cy = ((y1 + y2) // 2).astype(np.int32)
                cx_adj = cx + self.roi_x_start
                cy_adj = cy + self.roi_y_start

                bx, by, bw, bh = self.region_bbox
                in_bbox_mask = (
                    (cx_adj >= bx) & (cx_adj < bx + bw) &
                    (cy_adj >= by) & (cy_adj < by + bh)
                )
                candidate_idx = np.nonzero(in_bbox_mask)[0]
                valid_list = []
                for idx in candidate_idx:
                    if cv2.pointPolygonTest(self.region_pts, (int(cx_adj[idx]), int(cy_adj[idx])), False) >= 0:
                        valid_list.append(idx)

                valid_indices = np.asarray(valid_list, dtype=np.int32)
                for idx in valid_indices:
                    track_id = self.ids[idx]
                    class_id = self.classes[idx]
                    speed_id = self.speeds.get(track_id, 0)
                    color = self.color_motor if class_id == 1 else self.color_car
                    cv2.putText(
                        self.frame_predict, f"{speed_id} km/h",
                        (int(cx[idx]) - 50, int(cy[idx]) - 15),
                        self.font, self.font_scale, color, self.font_thickness
                    )
                    cv2.circle(self.frame_predict, (int(cx[idx]), int(cy[idx])), 5, color, -1)

            self.frame_output[self.roi_y_start:, self.roi_x_start:] = self.frame_predict
            cv2.polylines(self.frame_output, [self.region_pts], isClosed=True, color=self.color_region, thickness=4)

        except Exception as e:
            print(f"Lỗi khi vẽ {self.name}: {e}")

    def process_on_single_video(self):
        """Vòng lặp chính: đọc video → xử lý từng frame → loop lại khi hết."""
        cam = cv2.VideoCapture(self.path_video)
        if not cam.isOpened():
            print(f"Không thể mở video: {self.path_video}")
            return

        try:
            while True:
                check, cap = cam.read()
                if not check:
                    cam.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                time_now = datetime.now()
                delta = (time_now - self.time_pre_for_fps).total_seconds()
                fps = round(1 / delta) if delta > 0 else 0
                self.time_pre_for_fps = time_now

                cvzone.putTextRect(
                    cap, f"FPS: {fps}", (516, 20),
                    scale=1.1, thickness=2,
                    colorT=(0, 255, 100), colorR=(50, 50, 50),
                    border=2, colorB=(255, 255, 255)
                )

                self.process_single_frame(cap)

                if self.show:
                    cv2.imshow(self.name, self.frame_output)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

        except KeyboardInterrupt:
            print(f"Đã dừng {self.name}")
        except Exception as e:
            print(f"Lỗi {self.name}: {e}")
        finally:
            cam.release()
            if self.show:
                cv2.destroyAllWindows()


class RoadDetector(RoadDetectorBase):
    """Concrete class — ghi kết quả vào Manager.dict() để share giữa các process."""

    def __init__(self, path_video, meter_per_pixel, info_dict, frame_dict, region, **kwargs):
        """
        Args:
            info_dict (Manager().dict()): Dict chia sẻ thông tin phương tiện giữa processes
            frame_dict (Manager().dict()): Dict chia sẻ frame bytes giữa processes
        """
        super().__init__(path_video, meter_per_pixel, region=region, **kwargs)
        self.info_dict = info_dict
        self.frame_dict = frame_dict

    @override
    def update_for_frame(self):
        """Ghi frame hiện tại (dạng bytes) vào frame_dict để API đọc."""
        try:
            # Encode NumPy array sang JPEG ngay trong child process!
            # Tiết kiệm chi phí serialize (IPC pickle array 1MB xuống còn string bytes ~50KB)
            # và giải phóng Main process không phải encode liên tục.
            success, jpeg = cv2.imencode('.jpg', self.frame_output, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if success:
                self.frame_dict["frame"] = jpeg.tobytes()
        except Exception as e:
            print(f"Lỗi update_for_frame {self.name}: {e}")

    @override
    def update_for_vehicle(self):
        """Ghi thông tin phương tiện (count, speed) vào info_dict để API đọc."""
        try:
            self.info_dict["count_car"] = self.count_car_display
            self.info_dict["count_motor"] = self.count_motor_display
            self.info_dict["speed_car"] = self.speed_car_display
            self.info_dict["speed_motor"] = self.speed_motor_display
        except Exception as e:
            print(f"Lỗi update_for_vehicle {self.name}: {e}")
