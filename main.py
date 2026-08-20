# services/travel_detection.py

from math import radians, sin, cos, sqrt, atan2


class TravelDetector:

    EARTH_RADIUS_KM = 6371

    @classmethod
    def distance(
        cls,
        lat1,
        lon1,
        lat2,
        lon2
    ):

        lat1 = radians(lat1)
        lat2 = radians(lat2)

        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = (
            sin(delta_lat / 2) ** 2
            +
            cos(lat1)
            * cos(lat2)
            * sin(delta_lon / 2) ** 2
        )

        c = 2 * atan2(
            sqrt(a),
            sqrt(1 - a)
        )

        return cls.EARTH_RADIUS_KM * c

    @classmethod
    def detect(
        cls,
        previous,
        current,
        hours
    ):

        distance = cls.distance(
            previous["lat"],
            previous["lon"],
            current["lat"],
            current["lon"]
        )

        if hours <= 0:
            return {
                "suspicious": True,
                "distance_km": distance
            }

        speed = distance / hours

        suspicious = speed > 900

        return {
            "distance_km": round(distance, 2),
            "required_speed_kmh": round(speed, 2),
            "suspicious": suspicious
        }