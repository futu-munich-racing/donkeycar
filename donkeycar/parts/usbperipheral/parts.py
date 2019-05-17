from .protocol import Protocol, SensorPacket


class SteeringControl:
    def __init__(self, protocol: Protocol):
        self._protocol = protocol

    def run(self, **kwargs):
        print(kwargs)
        # self._protocol.setSteering(int(steering))


class ThrottleControl:
    def __init__(self, protocol: Protocol):
        self._protocol = protocol

    def run(self, **kwargs):
        print(kwargs)
        # self._protocol.setThrottle(int(throttle))


class IMUSensor:
    def __init__(self, protocol: Protocol):
        self._protocol = protocol
        self.data = None

    def run(self,):
        return self.data['accel'][0], self.data['accel'][1], self.data['accel'][2], self.data['gyro'][0], self.data['gyro'][1], self.data['gyro'][2], self.data['magneto'][0], self.data['magneto'][1], self.data['magneto'][2]


class DistanceSensor:
    def __init__(self, protocol: Protocol):
        self._protocol = protocol
        self.data = None

    def run(self,):
        return self.data['left'], self.data['right'], self.data['center']


class PeripheralPart:
    def __init__(self):
        self._protocol = Protocol(packetHandler=self._updateValues)
        self._steering = SteeringControl(self._protocol)
        self._throttle = ThrottleControl(self._protocol)
        self._imu = IMUSensor(self._protocol)
        self._distance = DistanceSensor(self._protocol)

    def getSteeringPart(self):
        return self._steering

    def getThrottlePart(self):
        return self._throttle

    def getIMUPart(self):
        return self._imu

    def getDistancePart(self):
        return self._distance

    def _updateValues(self, packet: SensorPacket):
        # self._current = packet
        self._imu.data = {
            'accel': packet.acceleration,
            'gyro': packet.gyro,
            'magneto': packet.magneto
        }
        self._distance.data = {
            'left': packet.distance[0],
            'right': packet.distance[1],
            'center': packet.distance[2]
        }

    def update(self):
        self._protocol.start()

    def run_threaded(self,):
        pass
