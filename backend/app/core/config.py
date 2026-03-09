import os
import numpy as np
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # Frontend
    URL_FRONTEND: str = "http://localhost:5173"

    # AI / Chatbot
    GOOGLE_API_KEY: str = ""

    # Video Processing
    DEVICE: str = "cpu"
    MODELS_PATH: str = "./ai_models/best_int8_openvino_model"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


# ─────────────────────────────────────────────
# Video / Road configuration
# ─────────────────────────────────────────────

class RoadConfig:
    """Cấu hình các tuyến đường được giám sát."""

    REGIONS: List[np.ndarray] = [
        np.array([[50, 400], [50, 265], [370, 130], [540, 130], [490, 400]]),
        np.array([[230, 400], [90, 260], [350, 200], [600, 320], [600, 400]]),
        np.array([[50, 400], [50, 340], [400, 125], [530, 185], [470, 400]]),
        np.array([[140, 400], [400, 200], [550, 200], [530, 400]]),
        np.array([[50, 400], [50, 320], [390, 130], [550, 220], [480, 400]]),
    ]

    PATH_VIDEOS: List[str] = [
        "./video_test/Văn Quán.mp4",
        "./video_test/Văn Phú.mp4",
        "./video_test/Nguyễn Trãi.mp4",
        "./video_test/Ngã Tư Sở.mp4",
        "./video_test/Đường Láng.mp4",
    ]

    METER_PER_PIXELS: List[float] = [0.1, 0.15, 0.42, 0.15, 0.05]


road_config = RoadConfig()


# ─────────────────────────────────────────────
# Traffic density thresholds (per road)
# ─────────────────────────────────────────────

TRAFFIC_THRESHOLDS = {
    "Đường Láng":    {"v": 13, "c1": 17, "c2": 26},
    "Ngã Tư Sở":    {"v": 17, "c1": 45, "c2": 57},
    "Nguyễn Trãi":  {"v": 30, "c1": 25, "c2": 35},
    "Văn Quán":     {"v": 10, "c1": 10, "c2": 17},
    "Văn Phú":      {"v": 15, "c1": 18, "c2": 26},
}

DEFAULT_THRESHOLD = {"v": 15, "c1": 15, "c2": 25}


def get_threshold(road_name: str) -> dict:
    return TRAFFIC_THRESHOLDS.get(road_name, DEFAULT_THRESHOLD)
