import serial
import binascii
from datetime import datetime
import keyboard
from websockets.sync.client import connect

class SerialDataProcessor:
    def __init__(self, port='COM8', baudrate=115200):
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=0)
        print(f"Connected to: {self.ser.portstr}")
        self.flag = False
        self.buff = []
        self.buff_str = b''
        self.data_length = 999
        self.read_mode = True
        self.tag_found = False
        self.uhf_db = []

    def calculate_checksum(self, uBuff):
        uSum = 0
        for byte in uBuff:
            uSum += int(binascii.hexlify(byte).decode('utf-8'), 16) & 0xFF
        uSum = ((~uSum) + 1) & 0xFF
        return uSum

    def verify_checksum(self, data, checksum):
        print(f'PASS: {data == checksum}')
        return data == checksum

    def send_information(self, payload):
        with connect("ws://127.0.0.1:1880/ws/live") as websocket:
            websocket.send(payload)

    def process_serial_data(self):
        count = 0
        while self.ser.is_open:
            now = datetime.now()

            if self.ser.in_waiting != 0 and self.read_mode:
                s = self.ser.read()
                self.buff.append(s)

                if len(self.buff) == 2:
                    hex_string = binascii.hexlify(self.buff[0] + self.buff[1]).decode('utf-8')
                    self.flag = True

                if len(self.buff) == 4:
                    hex_string = binascii.hexlify(self.buff[2] + self.buff[3]).decode('utf-8')
                    self.data_length = int(hex_string, 16) + 3

                if len(self.buff) == self.data_length:
                    # Process data
                    spess = b''
                    for s in self.buff[self.data_length - 1]:
                        spess = s
                    print(f'RSSI: {spess}')

                    for s in self.buff[18:self.data_length - 1]:
                        self.buff_str += s

                    hex_string = binascii.hexlify(self.buff_str).decode('utf-8')

                    if int(binascii.hexlify(self.buff[5]).decode('utf-8'), 16) == 69:
                        print(f'Tag found: {hex_string}')
                        self.tag_found = True
                        uhf = hex_string

                if len(self.buff) == self.data_length + 1:
                    result = self.calculate_checksum(self.buff[:-1])
                    if self.verify_checksum(result, int(binascii.hexlify(self.buff[-1]).decode('utf-8'), 16)):
                        self.send_information(uhf)
                        self.buff = []
                        self.data_length = 999
                        self.buff_str = b''
                        count += 1

            elif keyboard.is_pressed('q'):
                self.ser.close()
                break

            else:
                if now.second % 1 == 0:
                    print(f'Current second: {now.second}')
                    count = 0
                    self.uhf_db = []
                    time.sleep(1)

if __name__ == "__main__":
    processor = SerialDataProcessor()
    processor.process_serial_data()