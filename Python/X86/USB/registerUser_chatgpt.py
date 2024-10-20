import serial
import binascii
import streamlit as st
import keyboard
import json
from smartcard.scard import (
    SCardGetErrorMessage,
    SCARD_SCOPE_USER,
    SCARD_S_SUCCESS,
    SCARD_SHARE_SHARED,
    SCARD_PROTOCOL_T0,
    SCARD_PROTOCOL_T1,
    SCARD_CTL_CODE,
    SCardEstablishContext,
    SCardListReaders,
    SCardConnect,
    SCardControl
)

import time
import sys
from websockets.sync.client import connect

class RFIDReader:
    def __init__(self, serial_port='COM6', baud_rate=115200):
        self.ser = serial.Serial(port=serial_port, baudrate=baud_rate, timeout=0)
        self.nfc_found = False
        self.tag_found = False
        self.retry_counter = 0
        self.read_mode = True
        self.buff = []
        self.buff_str = b''
        self.rssi_buff = b''
        self.data_length = 999
        self.nfc = ''
        self.uhf = ''
        self.unknown_area = {}
        self.area = {}
        self.chiller_area = {}
        self.user_profile = {}
        self.stop_read_command = bytes.fromhex('53570003FF4014')
        self.start_read_command = bytes.fromhex('53570003FF4113') 

    def send_information(self, payload):
        with connect("ws://127.0.0.1:1880/ws/register") as websocket:
            websocket.send(json.dumps(payload))
            message = websocket.recv()
            print(f"Received: {message}")

    def calculate_checksum(self, uBuff):
        uSum = 0
        print(uBuff)
        for byte in uBuff:
            uSum += int(binascii.hexlify(byte).decode('utf-8'), 16) & 0xFF
        uSum = ((~uSum) + 1) & 0xFF
        return uSum

    def verify_checksum(self, data, checksum):
        print(f'PASS : {data == checksum}')
        return data == checksum

    def get_user(self, uid):
        if uid in Dabase:
            return Dabase[uid]
        else:
            return 'unknown'

    def get_result(self):
        return 'kenghzou'

    def run(self):
        print("Connected to: " + self.ser.portstr)

        while True:
            try:
                if not self.nfc_found:
                    hresult, hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
                    if hresult == SCARD_S_SUCCESS:
                        hresult, readers = SCardListReaders(hcontext, [])
                        if len(readers) > 0:
                            reader = readers[0]
                            hresult, hcard, dwActiveProtocol = SCardConnect(hcontext, reader,
                                                                             SCARD_SHARE_SHARED,
                                                                             SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)

                            apdu_cmd = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                            if hcard > 0:
                                hresult, response = SCardControl(hcard, SCARD_CTL_CODE(3500), apdu_cmd)
                                if hresult != SCARD_S_SUCCESS:
                                    print(SCardGetErrorMessage(hresult))

                                self.nfc = ''.join(map(lambda x: f'{x:02x}', response[:-2])).replace('0x', '')
                                print(f'NFC: {self.nfc}')
                                self.nfc = self.get_user(self.nfc)
                                self.nfc_found = True
                                print('Found NFC')

                elif self.nfc_found and not self.tag_found:
                    write_buff = self.start_read_command
                    print(write_buff)
                    self.ser.write(write_buff)

                    while self.ser.is_open:
                        if self.ser.in_waiting != 0 and self.read_mode:
                            s = self.ser.read()
                            self.buff.append(s)

                            if len(self.buff) == 2:
                                hex_string = binascii.hexlify(self.buff[0] + self.buff[1]).decode('utf-8')
                                print(f'HEAD : {hex_string}')

                            if len(self.buff) == 4:
                                hex_string = binascii.hexlify(self.buff[2] + self.buff[3]).decode('utf-8')
                                self.data_length = int(hex_string, 16) + 3
                                print(f'Length : {hex_string}')

                            if len(self.buff) == self.data_length:
                                print(self.data_length)
                                print(binascii.hexlify(self.buff[5]).decode('utf-8'))

                                rssi = 0
                                for s in self.buff[self.data_length - 1]:
                                    rssi = s

                                print(f'RSSI ={rssi}')

                                for s in self.buff[18:self.data_length - 1]:
                                    self.buff_str += s

                                hex_string = binascii.hexlify(self.buff_str).decode('utf-8')

                                print(f'Data : {hex_string}')

                                if int(binascii.hexlify(self.buff[5]).decode('utf-8'), 16) == 69:
                                    print('Tag found')
                                    self.uhf = hex_string

                            if len(self.buff) == self.data_length + 1:
                                result = self.calculate_checksum(self.buff[:-1])
                                if self.verify_checksum(result,
                                                        int(binascii.hexlify(self.buff[-1]).decode('utf-8'), 16)):
                                    self.buff = []
                                    self.data_length = 999
                                    self.buff_str = b''
                                    print('Done checksum')
                                    self.tag_found = True
                                    self.read_mode = False

                        else:
                            time.sleep(1)
                            print('Am I here')

                            if self.retry_counter > 2:
                                print('-------------------RESET----------------')
                                self.tag_found = False
                                self.nfc_found = False
                                self.read_mode = False
                                self.buff = []
                                self.data_length = 999
                                self.retry_counter = 0
                                self.buff_str = b''
                                write_buff = bytes.fromhex('53570003FF4014')
                                self.ser.write(write_buff)
                                break
                            else:
                                self.retry_counter += 1

                elif self.tag_found:
                    print('============Stopped===============')
                    write_buff = self.stop_read_command
                    self.user_profile[self.uhf] = self.nfc

                    user = f'{self.nfc},{self.uhf}'
                    print(f'Binding:{user}')
                    self.send_information(self.user_profile)
                    self.user_profile = {}
                    self.ser.write(write_buff)
                    self.nfc_found = False
                    self.tag_found = False
                    self.read_mode = True
                    time.sleep(2)
                    break

                if keyboard.is_pressed('q'):
                    self.chiller_area = {'c38b2211022ef3010f0101e2004707a7506821df3c010c': 'Keng Hzou'}
                    print('Keng Hzou Moved to Chiller Area')
                    time.sleep(3)

            except KeyboardInterrupt:
                print('Close serial!')
                self.ser.close()
                break

        self.ser.close()
        sys.exit()


if __name__ == "__main__":
    rfid_reader = RFIDReader()
    rfid_reader.run()