# services/user_profile.py

class UserBehaviorProfile:

    def __init__(self):
        self.transaction_count = 0
        self.total_amount = 0
        self.average_amount = 0
        self.known_devices = set()
        self.known_locations = set()

    def update(
        self,
        amount,
        device_id=None,
        location=None
    ):

        self.transaction_count += 1
        self.total_amount += amount

        self.average_amount = (
            self.total_amount /
            self.transaction_count
        )

        if device_id:
            self.known_devices.add(device_id)

        if location:
            self.known_locations.add(location)

    def is_new_device(self, device_id):

        return device_id not in self.known_devices

    def is_new_location(self, location):

        return location not in self.known_locations