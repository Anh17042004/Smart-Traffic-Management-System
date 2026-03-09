"""
api/v1/traffic.py
Refactored từ api_vehicles_frames.py

Endpoints:
  GET  /roads                    → danh sách tuyến đường (public)
  GET  /roads/{name}/info        → metrics tuyến đường (public)
  GET  /roads/{name}/frame       → JPEG frame hiện tại (yêu cầu auth)
  WS   /ws/roads/{name}/frames   → stream JPEG frames (yêu cầu auth)
  WS   /ws/roads/{name}/info     → stream metrics JSON (yêu cầu auth)
"""
import asyncio

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response

from app.api.v1.dependencies import get_current_user, get_current_user_ws
from app.models.user import User
from app.utils.transport_utils import enrich_info_with_thresholds

router = APIRouter()


def _get_pool(request: Request):
    """Lấy VideoProcessorPool từ app.state (được khởi tạo trong lifespan)."""
    return request.app.state.processor


# ─────────────────────────────────────────────
# REST Endpoints
# ─────────────────────────────────────────────

@router.get("/roads", summary="Danh sách tuyến đường đang giám sát (public)")
async def get_road_names(request: Request):
    """Trả về list tên tuyến đường. Không cần đăng nhập.
    
    Frontend dùng để load danh sách đường ngay khi vào trang.
    """
    pool = _get_pool(request)
    return JSONResponse(content={"road_names": pool.get_names()})


@router.get("/roads/{road_name}/info", summary="Metrics tuyến đường (public)")
async def get_road_info(road_name: str, request: Request):
    """Trả về thông tin xe cộ của tuyến đường.

    Response:
        count_car: Số ô tô
        count_motor: Số xe máy
        speed_car: Tốc độ TB ô tô (km/h)
        speed_motor: Tốc độ TB xe máy (km/h)
        density_status: "Thông thoáng" | "Đông đúc" | "Tắc nghẽn"
        speed_status: "Nhanh chóng" | "Chậm chạp"
    """
    pool = _get_pool(request)
    data = await asyncio.to_thread(pool.get_info_road, road_name)
    if not data:
        return JSONResponse(content={"error": "Tuyến đường không tồn tại"}, status_code=404)
    enriched = enrich_info_with_thresholds(dict(data), road_name)
    return JSONResponse(content=enriched)


@router.get("/roads/{road_name}/frame", summary="Frame JPEG hiện tại (cần đăng nhập)")
async def get_road_frame(
    road_name: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Trả về 1 JPEG frame hiện tại của tuyến đường.
    
    Yêu cầu: Authorization: Bearer <token>
    """
    pool = _get_pool(request)
    frame_bytes = await asyncio.to_thread(pool.get_frame_road, road_name)
    if not frame_bytes:
        return JSONResponse(content={"error": "Không lấy được frame"}, status_code=500)
    return Response(content=frame_bytes, media_type="image/jpeg")


# ─────────────────────────────────────────────
# WebSocket Streaming
# ─────────────────────────────────────────────

@router.websocket("/ws/roads/{road_name}/frames")
async def ws_stream_frames(
    websocket: WebSocket,
    road_name: str,
    current_user: User = Depends(get_current_user_ws),
):
    """WebSocket stream JPEG frames (~30fps).
    
    Auth: gửi token qua query param: ?token=...
    Client nhận: binary bytes JPEG, hiển thị bằng <img src="blob:...">
    """
    pool = websocket.app.state.processor
    await websocket.accept()
    try:
        while True:
            frame_bytes = await asyncio.to_thread(pool.get_frame_road, road_name)
            if frame_bytes:
                await websocket.send_bytes(frame_bytes)
            await asyncio.sleep(1 / 30)  # 30 FPS cap
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS frames error: {e}")
        await websocket.close()


@router.websocket("/ws/roads/{road_name}/info")
async def ws_stream_info(
    websocket: WebSocket,
    road_name: str,
    current_user: User = Depends(get_current_user_ws),
):
    """WebSocket stream metrics JSON (~20fps).
    
    Auth: gửi token qua query param: ?token=...
    Client nhận: JSON {count_car, count_motor, speed_car, speed_motor, density_status, ...}
    """
    pool = websocket.app.state.processor
    await websocket.accept()
    try:
        while True:
            data = await asyncio.to_thread(pool.get_info_road, road_name)
            enriched = enrich_info_with_thresholds(dict(data), road_name) if data else {}
            await websocket.send_json(enriched)
            await asyncio.sleep(1 / 20)  # 20 updates/s
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close()
