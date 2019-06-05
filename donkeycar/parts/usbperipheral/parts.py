from .protocol import Protocol, SensorPacket


class IMUSensor:
    def __init__(self, protocol: Protocol):
        self._protocol = protocol
        self._data = {
            'orientation': [0, 0, 0],
            'rotation': [0, 0, 0],
            'acceleration': [0, 0, 0],
            'calibration': [0,0,0,0]
        }

    def updateData(self, data):
        self._data = data

    def run(self,):
        return self._data['orientation'][0]/100.0, self._data['orientation'][1]/100.0, self._data['orientation'][2]/100.0, self._data['rotation'][0]/100.0, self._data['rotation'][1]/100.0, self._data['rotation'][2]/100.0, self._data['acceleration'][0]/100.0, self._data['acceleration'][1]/100.0, self._data['acceleration'][2]/100.0


class DistanceSensor:
    def __init__(self, protocol: Protocol):
        self._protocol = protocol
        self._data = [0, 0, 0]

    def updateData(self, data):
        self._data = data

    def run(self,):
        return self._data[0], self._data[1], self._data[2]


class PeripheralPart:
    def __init__(self):
        self._protocol = Protocol(packetHandler=self._updateValues)
        self._imu = IMUSensor(self._protocol)
        self._distance = DistanceSensor(self._protocol)

    def getIMUPart(self):
        return self._imu

    def getDistancePart(self):
        return self._distance

    def _updateValues(self, packet: SensorPacket):
        self._imu.updateData({
            'orientation': packet.orientation,
            'rotation': packet.rotation,
            'acceleration': packet.acceleration,
            'calibration': packet.calibration
        })
        self._distance.updateData(packet.distance)

    def update(self):
        self._protocol.start()

    def run_threaded(self,):
        pass
