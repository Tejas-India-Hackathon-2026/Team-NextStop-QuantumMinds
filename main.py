# services/geofence.py

from math import radians, sin, cos, sqrt, atan2


class GeoFence:

    EARTH_RADIUS = 6371

    def distance(
        self,
        lat1,
        lon1,
        lat2,
        lon2
    ):

        lat1 = radians(lat1)
        lat2 = radians(lat2)

        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)

        a = (
            sin(dlat / 2) ** 2
            +
            cos(lat1)
            * cos(lat2)
            * sin(dlon / 2) ** 2
        )

        c = 2 * atan2(
            sqrt(a),
            sqrt(1 - a)
        )

        return self.EARTH_RADIUS * c

    def inside(
        self,
        user_lat,
        user_lon,
        center_lat,
        center_lon,
        radius_km
    ):

        distance = self.distance(
            user_lat,
            user_lon,
            center_lat,
            center_lon
        )

        return {
            "inside": distance <= radius_km,
            "distance_km": round(distance, 2),
            "radius_km": radius_km
        }s