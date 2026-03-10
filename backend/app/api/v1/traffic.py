import asyncio

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response

from app.core.dependencies import get_current_user, get_current_user_ws
from app.models.user import User
from app.services.traffic.traffic_services import TrafficService
from app.utils.transport_utils import enrich_info_with_thresholds


router = APIRouter()

def _get_service(request: Request) -> TrafficService:
    """
    Lấy TrafficService từ app.state.
    """
    pool = request.app.state.processor  #khởi tạo VideoProcessorPool trong lifespan
    return TrafficService(pool)


# REST API
@router.get("/", summary="Danh sách tuyến đường đang giám sát (public)")
async def get_road_names(request: Request):
    service = _get_service(request)
    roads = service.get_roads()
    return JSONResponse(
        content={
            "roads": roads,
            "total": len(roads)
        }
    )


@router.get("/{road_name}/info", summary="Metrics tuyến đường (public)")
async def get_road_info(road_name: str, request: Request):
    service = _get_service(request)
    data = await asyncio.to_thread(
        service.get_traffic_info,
        road_name
    )
    if not data:
        return JSONResponse(
            content={"error": "Tuyến đường không tồn tại"},
            status_code=404
        )
    enriched = enrich_info_with_thresholds(
        dict(data),
        road_name
    )
    return JSONResponse(content=enriched)


@router.get(
    "/{road_name}/frame",
    summary="Frame JPEG hiện tại (cần đăng nhập)"
)
async def get_road_frame(
    road_name: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    service = _get_service(request)
    frame_bytes = await asyncio.to_thread(
        service.get_camera_frame,
        road_name
    )
    if not frame_bytes:
        return JSONResponse(
            content={"error": "Không lấy được frame"},
            status_code=500
        )
    return Response(
        content=frame_bytes,
        media_type="image/jpeg"
    )


# WebSocket Streaming
@router.websocket("/ws/roads/{road_name}/frames")
async def ws_stream_frames(
    websocket: WebSocket,
    road_name: str,
    current_user: User = Depends(get_current_user_ws),
):
    service = TrafficService(websocket.app.state.processor)
    await websocket.accept()
    try:
        while True:
            frame_bytes = await asyncio.to_thread(
                service.get_camera_frame,
                road_name
            )
            if frame_bytes:
                await websocket.send_bytes(frame_bytes)
            await asyncio.sleep(1 / 30)  # 30 FPS cap
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS frame error: {e}")
        await websocket.close()


@router.websocket("/ws/roads/{road_name}/info")
async def ws_stream_info(
    websocket: WebSocket,
    road_name: str,
    current_user: User = Depends(get_current_user_ws),
):
    service = TrafficService(websocket.app.state.processor)
    await websocket.accept()
    try:
        while True:
            data = await asyncio.to_thread(
                service.get_traffic_info,
                road_name
            )
            enriched = (
                enrich_info_with_thresholds(dict(data), road_name)
                if data else {}
            )
            await websocket.send_json(enriched)
            await asyncio.sleep(1 / 20)  # 20 updates/s
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()