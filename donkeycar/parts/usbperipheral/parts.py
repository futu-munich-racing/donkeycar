from .protocol import Protocol, SensorPacket
from .madgwick.madgwickahrs import MadgwickAHRS


def convertUnit(values, factor):
    return [
        values[0]*factor,
        values[1]*factor,
        values[2]*factor
    ]


class ControlPart:
    def __init__(self, protocol: Protocol):
        self._protocol = protocol

    def run(self, steering, throttle):
        steering = int(90 + (steering * 60))
        throttle = int(1500 + (throttle * -500))
        if steering != 90 or throttle != 1500:
            print('Steering: {0}, Throttle: {1}'.format(steering, throttle))
        self._protocol.sendControlPacket(steering, throttle)


class IMUSensor:
    def __init__(self, protocol: Protocol):
        self._protocol = protocol
        self._data = {
            'accel': [0, 0, 0],
            'gyro': [0, 0, 0],
            'magneto': [0, 0, 0]
        }
        self._madgwick = MadgwickAHRS(sampleperiod=1/40)

    def updateData(self, data):
        self._data = data
        self._madgwick.update(
            self._data['gyro'], self._data['accel'], self._data['magneto'])

    def run(self,):
        #print(self._madgwick.quaternion.to_euler_angles())
        #print(self._data)
        return self._data['accel'][0], self._data['accel'][1], self._data['accel'][2], self._data['gyro'][0], self._data['gyro'][1], self._data['gyro'][2], self._data['magneto'][0], self._data['magneto'][1], self._data['magneto'][2]


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
        self._control = ControlPart(self._protocol)
        self._imu = IMUSensor(self._protocol)
        self._distance = DistanceSensor(self._protocol)

    def getControlPart(self):
        return self._control

    def getIMUPart(self):
        return self._imu

    def getDistancePart(self):
        return self._distance

    def _updateValues(self, packet: SensorPacket):
        self._imu.updateData({
            'accel': convertUnit(packet.acceleration, 0.061), # convert to mg (g != gramm, it's force)
            'gyro': convertUnit(packet.gyro, 4.375), #  convert to mdps
            'magneto': convertUnit(packet.magneto, 1.0/6842.0) # convert to mgauss
        })
        self._distance.updateData(packet.distance)

    def update(self):
        self._protocol.start()

    def run_threaded(self,):
        pass
