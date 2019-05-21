import asyncio
import serial_asyncio
from sliplib import Driver as SLIPDriver
from zlib import crc32
import struct


def calcChecksum(data):
    return (crc32(data) & 0xffffffff).to_bytes(4, 'little')


slipDriver = SLIPDriver()


class SensorPacket:
    def __init__(self, data):
        if isinstance(data, int):
            self.valid = False
            return
        payload = data[0:24]
        checksum = data[24:28]
        calculatedChecksum = calcChecksum(payload)

        self.valid = checksum == calculatedChecksum
        if not self.valid:
            return

        tmp = list(struct.unpack('<HHHHHHHHHHHH', payload))

        self.distance = tmp[0:3]
        self.magneto = tmp[3:6]
        self.acceleration = tmp[6:9]
        self.gyro = tmp[9:12]

    def __str__(self):
        if not self.valid:
            return 'SensorMessage: Invalid!'
        return 'SensorMessage:\nDist: {0}\nCompass: {1}\nAccel: {2}\nGyro: {3}'.format(
            self.distance,
            self.magneto,
            self.acceleration,
            self.gyro
        )


class Serial(asyncio.Protocol):
    def __init__(self, packetHandler=lambda: None):
        super().__init__()
        self._packetHandler = packetHandler

    def connection_made(self, transport):
        self._transport = transport
        self._buffer = bytearray()

    async def send(self, packet):
        self._transport.serial.write(packet)

    def data_received(self, data):
        self._buffer += data
        if len(self._buffer) >= 28:
            try:
                data = slipDriver.receive(self._buffer)
            except:
                pass
            if len(data) > 0:
                for rawPacket in data:
                    packet = SensorPacket(rawPacket)
                    if packet.valid:
                        self._packetHandler(packet)


class Protocol:
    def __init__(self, device='/dev/ttyACM0', baud=115200, packetHandler=lambda: None):
        self._loop = asyncio.get_event_loop()
        self._serialProtocol = Serial(packetHandler)
        self._serialConnection = serial_asyncio.create_serial_connection(
            self._loop, lambda: self._serialProtocol, device, baudrate=baud)
        asyncio.ensure_future(self._serialConnection)

    def start(self):
        self._loop.run_forever()

    def sendControlPacket(self, steering, throttle):
        payload = bytearray(struct.pack('<HH', steering, throttle))
        checksum = calcChecksum(payload)
        payload.extend(checksum)
        self._loop.create_task(
            self._serialProtocol.send(slipDriver.send(payload)))
