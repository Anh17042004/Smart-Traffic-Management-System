class TrafficService:

    def __init__(self, pool):

        self.pool = pool

    def get_roads(self):

        return self.pool.get_names()

    def get_traffic_info(self, road_name):

        data = self.pool.get_info_road(road_name)

        if not data:
            return None

        count_car = data.get("count_car", 0)
        count_motor = data.get("count_motor", 0)

        speed_car = data.get("speed_car", 0)
        speed_motor = data.get("speed_motor", 0)

        total = count_car + count_motor

        density = "low"

        if total > 80:
            density = "high"
        elif total > 40:
            density = "medium"

        return {
            "road": road_name,
            "count_car": count_car,
            "count_motor": count_motor,
            "speed_car": speed_car,
            "speed_motor": speed_motor,
            "density_status": density
        }

    def get_camera_frame(self, road_name):

        return self.pool.get_frame_road(road_name)