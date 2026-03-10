import json
from typing import Annotated
from langchain_core.tools import tool


def build_tools(pool):

    @tool
    def get_roads() -> str:
        """
        Trả danh sách các tuyến đường đang được hệ thống giám sát.
        """

        roads = pool.get_names()

        return json.dumps(
            {"status": "success", "roads": roads},
            ensure_ascii=False
        )

    @tool
    def get_traffic_status(
        road_name: Annotated[str, "Tên chính xác của tuyến đường"]
    ) -> str:
        """
        Lấy dữ liệu giao thông realtime của một tuyến đường.
        """

        data = pool.get_info_road(road_name)

        if not data:
            return json.dumps(
                {"status": "not_found", "road": road_name},
                ensure_ascii=False
            )

        return json.dumps(
            {
                "status": "success",
                "road": road_name,
                "data": data
            },
            ensure_ascii=False
        )

    @tool
    def get_camera_frame(
        road_name: Annotated[str, "Tên chính xác của tuyến đường"]
    ) -> str:
        """
        Trả URL ảnh camera của tuyến đường.
        """

        return json.dumps(
            {
                "status": "success",
                "road": road_name,
                "frame_url": f"/api/v1/roads/{road_name}/frame"
            },
            ensure_ascii=False
        )

    return [
        get_roads,
        get_traffic_status,
        get_camera_frame
    ]