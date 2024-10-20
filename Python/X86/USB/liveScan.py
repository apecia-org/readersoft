import serial
import binascii
import time
import keyboard
from datetime import datetime
import asyncio
from websockets.sync.client import connect
#from websocket import create_connection

# Get current date and time
import json
def calculate_checksum(uBuff):
    uSum = 0
    #print(uBuff)
    for byte in uBuff:
        uSum += int(binascii.hexlify(byte).decode('utf-8'),16) & 0xFF # Access the first byte of each bytes object
    uSum = ((~uSum) + 1)& 0xFF
    return uSum   # Ensure the result is an 8-bit unsigned integer

def verify_checksum(data,checksum):
    print(f'PASS : {data==checksum}')
    return data==checksum
    
def sendInformation(payload):
    with connect("ws://127.0.0.1:1880/ws/live") as websocket:
        websocket.send(payload)
        #message = websocket.recv()
        #print(f"Received: {message}")

ser = serial.Serial(port='COM8',baudrate=115200,timeout=0)
#ser2 = serial.Serial(port='COM6',baudrate=115200,timeout=0)
print("connected to: " + ser.portstr)
flag = False
count=1
buff = []
buff_str =b''
data_length = 999
read_mode = True
tag_found = False
chiller_area = {}
uhf_db = []
area={'c38b2211022ef3010f0101e2004707a7506821df3c010c': 'Keng Hzou', 'c38b2211022ef3010f0101168011011001110110010000': 'Kit Lin'}

count = 0
while(ser.is_open == True ):
    now = datetime.now()
    #if( ser2.in_waiting != 0 ):
    #    s2 = ser2.read()
    #    print('Result from Serial 2 {s2}')
    if( ser.in_waiting != 0 & read_mode):

        s = ser.read()
        buff.append(s)   
        #print(f'Current Buff{buff}')
        if(len(buff)==2):
            hex_string = binascii.hexlify(buff[0]+buff[1]).decode('utf-8')
            flag= True
            #print(f'HEAD : {hex_string}')
            #buff=[]
        if(len(buff)==4):
            hex_string = binascii.hexlify(buff[2]+buff[3]).decode('utf-8')
            data_length= int(hex_string,16) +3
            #print(f'length : {hex_string}')

        if(len(buff)==data_length):
            print('hello world')
            #print(data_length)
            #print(binascii.hexlify(buff[5]).decode('utf-8'))
            
            #dev sn
            #for s in buff[7:13]:
            #    buff_str += s
            
            #anntenna
            spess =b''
            for s in buff[data_length-1]:
                spess = s
            print(f'RSSI : {spess}')
            #print(f' Number of tags:{binascii.hexlify(spess).decode("utf-8")}')            
            for s in buff[18:data_length-1]:
                buff_str += s

            hex_string = binascii.hexlify(buff_str).decode('utf-8')

            #print(f'data : {hex_string}')
            if(int(binascii.hexlify(buff[5]).decode('utf-8'),16)==69):
                print(f'tag found : {hex_string}')
                tag_found=True
                uhf = hex_string
         
        if(len(buff)==data_length+1):
            print('hello world')
            result = calculate_checksum(buff[:-1]);
            if verify_checksum(result,int(binascii.hexlify(buff[-1]).decode('utf-8'),16)):
                sendInformation(uhf)
                #uhf_db.append(uhf)
                #uhf=''
            buff =[]
            data_length=999
            buff_str=b''
            #print('done checksum')
            count +=1
            #print(chiller_area)
            #if uhf =='c38b2211022ef3010f0101e2004707a7506821df3c010c':
            #    chiller_area[uhf] = 'Keng Hzou'
            #else:
            #    chiller_area[uhf] = 'Kit Lin'
                
            #print(hex_string)

            #print('no data')
            #ser.write(53 57 00 03 FF 10 44)


            #time.sleep(0.001)
            #print(f'Number of Tag Found {count}')
    
    elif keyboard.is_pressed('q'):   
        ser.close()
        break
    else:
        if now.second %1 ==0:
            print(f'current second: {now.second}')
            count=0
            #sendInformation(uhf_db)
            uhf_db=[]
            #unknown_area = dict(area.items() ^ chiller_area.items())
            
            #sendInformation({'common_area':unknown_area,'chiller_area':chiller_area})
           # print({'area':area,'unknown_area':unknown_area,'chiller_area':chiller_area})
            #print(f'UHF DB: {uhf_db}')
            
            time.sleep(1)
            chiller_area={}
        #else:
            #need to send websocket of empty area
            #chiller_area={}

ser.close()

