"""
utils/transport_utils.py
Các hàm tiện ích dùng chung cho video processing.
"""
import numpy as np
import cv2
import time
from typing import Any, Dict
from app.core.config import get_threshold


def convert_frame_to_byte(img: np.ndarray) -> bytes | None:
    """Chuyển numpy frame sang JPEG bytes để stream qua WebSocket."""
    if img is not None:
        try:
            _, jpeg = cv2.imencode('.jpg', img)
            return jpeg.tobytes()
        except Exception as e:
            print(f"Lỗi chuyển frame sang bytes: {e}")
    return None


def avg_none_zero(lst: list) -> int:
    non_zero = [x for x in lst if x != 0]
    return sum(non_zero) // len(non_zero) if non_zero else 0


def avg_none_zero_batch(
    car_counts: list,
    car_speeds: list,
    motor_counts: list,
    motor_speeds: list,
) -> tuple:
    """Tính trung bình bỏ qua 0 cho 4 list cùng lúc.
    Trả về tuple (count_car_avg, speed_car_avg, count_motor_avg, speed_motor_avg).
    """
    def _avg(lst):
        non_zero = [x for x in lst if x > 1]
        return (sum(non_zero) // len(non_zero)) if non_zero else 0

    return (
        _avg(car_counts),
        _avg(car_speeds),
        _avg(motor_counts),
        _avg(motor_speeds),
    )


def enrich_info_with_thresholds(data: Dict[str, Any], road_name: str) -> Dict[str, Any]:
    """Tính toán density_status và speed_status dựa trên ngưỡng của từng tuyến đường."""
    if not isinstance(data, dict):
        return data

    threshold = get_threshold(road_name)

    try:
        count_car = int(data.get("count_car", 0) or 0)
        count_motor = int(data.get("count_motor", 0) or 0)
        speed_car = float(data.get("speed_car", 0) or 0)
        speed_motor = float(data.get("speed_motor", 0) or 0)

        total = count_car + count_motor
        if total > threshold["c2"]:
            density_status = "Tắc nghẽn"
        elif total > threshold["c1"]:
            density_status = "Đông đúc"
        else:
            density_status = "Thông thoáng"

        avg_speed = (speed_car + speed_motor) / 2 if (speed_car or speed_motor) else 0
        speed_status = "Nhanh chóng" if avg_speed >= threshold["v"] else "Chậm chạp"

        data["density_status"] = density_status
        data["speed_status"] = speed_status
        data["thresholds"] = threshold

    except Exception:
        pass

    return data


def log(names: list, shared_data: dict) -> None:
    """In log thông tin các tuyến đường ra console (dùng trong process riêng)."""
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    try:
        while True:
            print(f"{BOLD}{CYAN}--- [Log {time.strftime('%H:%M:%S')}] ---{RESET}")
            for name in names:
                try:
                    if name in shared_data:
                        info = shared_data[name]['info']
                        print(
                            f"| {YELLOW}{name:<20}{RESET} | "
                            f"{GREEN}Ô tô: {info.get('count_car',0)} xe, {info.get('speed_car',0)} km/h "
                            f"| Xe máy: {info.get('count_motor',0)} xe, {info.get('speed_motor',0)} km/h{RESET} |"
                        )
                except Exception as e:
                    print(f"| {name} | Lỗi: {e} |")
            time.sleep(5)
    except KeyboardInterrupt:
        pass
