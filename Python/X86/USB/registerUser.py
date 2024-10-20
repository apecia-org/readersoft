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
import asyncio
from websockets.sync.client import connect
Dabase= {'ab6e7fff':'Kit Lin','0b1785ff':'Keng Hzou','2ea2173d':'James Wong','bb7a7eff':'Lam YS','3b028eff':'Eugene','fbed77ff':'Han Yang','db6450ff':'Chong'}

retry_counter =0
flag = False
count=1
buff = []
buff_str =b''
rssi_buff =b''
data_length = 999
read_mode = True
tag_found = False
nfc_found = False
nfc = ''
uhf = ''
unknown_area={}
area = {}
chiller_area ={}
user_profile = {}
ser = serial.Serial(port='COM6',baudrate=115200,timeout=0)

print("connected to: " + ser.portstr)

def sendInformation(payload):
    with connect("ws://127.0.0.1:1880/ws/register") as websocket:
        websocket.send(json.dumps(payload)) 
        message = websocket.recv()
        #user_profile = {}
        print(f"Received: {message}")


def calculate_checksum(uBuff):
    uSum = 0
    print(uBuff)
    for byte in uBuff:
        uSum += int(binascii.hexlify(byte).decode('utf-8'),16) & 0xFF # Access the first byte of each bytes object
    uSum = ((~uSum) + 1)& 0xFF
    return uSum   # Ensure the result is an 8-bit unsigned integer

def verify_checksum(data,checksum):
    print(f'PASS : {data==checksum}')
    return data==checksum

def get_user(uid):
    if uid in Dabase:
        return Dabase[uid]
    else:
        return 'unknown'
def get_result():
    return 'kenghzou'
    

while True:
    try:
        #print('connecting to nfc')
        if not nfc_found:
            hresult, hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
            if hresult == SCARD_S_SUCCESS:
                #print('connected')
                hresult, readers = SCardListReaders(hcontext, [])
                if len(readers) > 0:
                    reader = readers[0]
                    hresult, hcard, dwActiveProtocol = SCardConnect(hcontext, reader, SCARD_SHARE_SHARED, SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)

                    apdu_cmd = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                    if hcard>0:
                        hresult, response = SCardControl(hcard, SCARD_CTL_CODE(3500), apdu_cmd)
                        if hresult != SCARD_S_SUCCESS:
                            print(SCardGetErrorMessage(hresult))

                        #print('NFC tag UID is:', ''.join(map(lambda x: f'{x:02x}', response[:-2])).replace('0x', '')) 
                        nfc = ''.join(map(lambda x: f'{x:02x}', response[:-2])).replace('0x', '')
                        print(f'NFC: {nfc}')
                        nfc = get_user(nfc)
                        nfc_found=True 
                        print('found NFC')                        
        elif nfc_found & not tag_found:
            write_buff=bytes.fromhex('53570003FF4113')
            print(write_buff)
            ser.write(write_buff)
            while(ser.is_open == True):
               if( ser.in_waiting != 0 & read_mode):
                  
                  s = ser.read()
                  buff.append(s)   
                  if(len(buff)==2):
                     hex_string = binascii.hexlify(buff[0]+buff[1]).decode('utf-8')
                     flag= True
                     print(f'HEAD : {hex_string}')
                     #buff=[]
                  if(len(buff)==4):
                     hex_string = binascii.hexlify(buff[2]+buff[3]).decode('utf-8')
                     data_length= int(hex_string,16) +3
                     print(f'length : {hex_string}')
                        
                  if(len(buff)==data_length):
                     print(data_length)
                     print(binascii.hexlify(buff[5]).decode('utf-8'))
                     
                     rssi =0
                     for s in buff[data_length-1]:
                        rssi = s
                    # rssi = binascii.hexlify(rssi_buff).decode('utf-8')
                     print(f'RSSI ={rssi}')
                     for s in buff[18:data_length-1]:
                         buff_str += s
                     
                     hex_string = binascii.hexlify(buff_str).decode('utf-8')
                     
                     print(f'data : {hex_string}')
                     if(int(binascii.hexlify(buff[5]).decode('utf-8'),16)==69):
                        print('tag found')
                        uhf = hex_string
                     
                  if(len(buff)==data_length+1):
                     
                     result = calculate_checksum(buff[:-1]);
                     if(verify_checksum(result,int(binascii.hexlify(buff[-1]).decode('utf-8'),16))):
                        
                        buff =[]
                        data_length=999
                        buff_str=b''
                        print('done checksum')
                        tag_found=True
                        read_mode=False
                  #print(hex_string)
               
                 #print('no data')
                 #ser.write(53 57 00 03 FF 10 44)
               else:
                  #reset
                  time.sleep(1)
                  print('am i here')
                  if(retry_counter>2):
                     print('-------------------RESET----------------')
                     tag_found=False
                     nfc_found=False
                     read_mode=False
                     buff =[]
                     data_length=999
                     retry_counter=0
                     buff_str=b''
                     write_buff=bytes.fromhex('53570003FF4014')
                     ser.write(write_buff)
                     break
                  else:
                     retry_counter +=1
                  
        elif tag_found:
            print('============stopped===============')
            write_buff=bytes.fromhex('53570003FF4014')
            user_profile[uhf]=nfc
                  
            user = f'{nfc},{uhf}'
            print(f'binding:{user}')
            sendInformation(user_profile)
            user_profile={}
            ser.write(write_buff)
            #read_mode=False
            nfc_found=False
            tag_found=False
            read_mode=True
            #st.session_state['areaA'] += f'{nfc}'
            time.sleep(2)
            break

                
        if keyboard.is_pressed('q'):   
            chiller_area = {'c38b2211022ef3010f0101e2004707a7506821df3c010c': 'Keng Hzou'}
            print('Keng Hzou Moved to Chiller Area')
            time.sleep(3)
       
    except KeyboardInterrupt: 
        print('Close serial!') 
        ser.close()
        break
ser.close()
sys.exit()
