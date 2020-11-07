#!/usr/bin/env python

from __future__ import division
import cv2
import numpy as np
import socket
import struct
import math
import threading
import os
import sys
import time
import requests
import blynklib

BLYNK_AUTH = 'BW-OY7yiT4hVfh2BzXR_x3xy23j7Nkyr'

# initialize Blynk
blynk = blynklib.Blynk(BLYNK_AUTH)

class Threadblynk(threading.Thread):
    def __init__(self):
        super(Threadblynk, self).__init__()

    def run(self):
        while True:
            blynk.run()

# register handler for virtual pin V0 write event
@blynk.handle_event('write V0')
def write_virtual_pin_handler(pin, value):
    if value == ['1']:
        tvstate.turnTV()
        tvstate.changingtimer()

# register handler for virtual pin V2 write event
@blynk.handle_event('write V2')
def write_virtual_pin_handler(pin, value):
    if value == ['1']:
        requests.post('http://192.168.100.134:8080/api/module/youtube/youtubeload',
                    headers=headers, data=dataPlayload)

# register handler for virtual pin V3 write event
@blynk.handle_event('write V3')
def write_virtual_pin_handler(pin, value):
    if value == ['1']:
        requests.post('http://192.168.100.134:8080/api/module/youtube/youtubecontrol',
                    headers=headers, data=dataPlay)

# register handler for virtual pin V4 write event
@blynk.handle_event('write V4')
def write_virtual_pin_handler(pin, value):
    if value == ['1']:
        requests.post('http://192.168.100.134:8080/api/module/youtube/youtubecontrol',
                    headers=headers, data=dataPause)

class State():
    def turnTV(self):
        raise NotImplementedError("turnTV is abstractmethod")

    def changingtimer(self):
        raise NotImplementedError("changingtimer is abstractmethod")

    def facedetectedswitch(self):
        raise NotImplementedError("facedetectedswitch is abstractmethod")

    def getyoutube(self):
        raise NotImplementedError("getyoutube is abstractmethod")

class TVON(State):
    def turnTV(self):
        requests.post('http://192.168.100.134:8080/api/module/youtube/youtubecontrol',
                      headers=headers, data=dataPause)
        os.system('echo "standby 0" | cec-client -s')
        tvstate.change_state("tvon2off")

    def changingtimer(self):
        pass

    def facedetectedswitch(self):
        pass

    def getyoutube(self):
        requests.post('http://192.168.100.134:8080/api/module/youtube/youtubecontrol',
                      headers=headers, data=dataPlay)

class TVON2OFF(State):
    def turnTV(self):
        pass

    def changingtimer(self):
        time.sleep(30)
        tvstate.change_state("tvoff")

    def facedetectedswitch(self):
        pass

    def getyoutube(self):
        pass

class TVOFF(State):
    def turnTV(self):
        os.system('echo "on 0" | cec-client -s')
        tvstate.change_state("tvoff2on")

    def changingtimer(self):
        pass

    def facedetectedswitch(self):
        os.system('echo "on 0" | cec-client -s')
        tvstate.change_state("tvoff2on")

    def getyoutube(self):
        pass

class TVOFF2ON(State):
    def turnTV(self):
        pass

    def changingtimer(self):
        time.sleep(30)
        tvstate.change_state("tvon")

    def facedetectedswitch(self):
        pass

    def getyoutube(self):
        pass

class Context:
    def __init__(self):
        self.tvon = TVON()
        self.tvon2off = TVON2OFF()
        self.tvoff = TVOFF()
        self.tvoff2on = TVOFF2ON()
        self.state = self.tvon

    def change_state(self, switchsignal):
        if switchsignal == "tvon":
            self.state = self.tvon
        elif switchsignal == "tvon2off":
            self.state = self.tvon2off
        elif switchsignal == "tvoff":
            self.state = self.tvoff
        elif switchsignal == "tvoff2on":
            self.state = self.tvoff2on
        else:
            raise ValueError("change_state method must be in {}".format(["tvon", "tvon2off", "tvoff", "tvoff2on"]))

    def turnTV(self):
        self.state.turnTV()

    def changingtimer(self):
        self.state.changingtimer()

    def facedetectedswitch(self):
        self.state.facedetectedswitch()

    def getyoutube(self):
        self.state.getyoutube()

def facedetection():
    while True:
        data = b''
        data = s.recv(1024)

        if data == b'Face Detected':
            tvstate.facedetectedswitch()
            tvstate.changingtimer()
            tvstate.getyoutube()

class FrameSegment(object):
    """ 
    Object to break down image frame segment
    if the size of image exceed maximum datagram size 
    """
    MAX_DGRAM = 2**16
    MAX_IMAGE_DGRAM = MAX_DGRAM - 64 # extract 64 bytes in case UDP frame overflown
    def __init__(self, sock, port, addr="192.168.100.135"):
        self.s = sock
        self.port = port
        self.addr = addr

    def udp_frame(self, img):
        """ 
        Compress image and Break down
        into data segments 
        """
        compress_img = cv2.imencode('.jpg', img)[1]
        dat = compress_img.tostring()
        size = len(dat)
        count = math.ceil(size/(self.MAX_IMAGE_DGRAM))
        array_pos_start = 0
        while count:
            array_pos_end = min(size, array_pos_start + self.MAX_IMAGE_DGRAM)
            self.s.sendto(struct.pack("B", count) +
                dat[array_pos_start:array_pos_end], 
                (self.addr, self.port)
                )
            array_pos_start = array_pos_end
            count -= 1

def sendFrame():
    fs = FrameSegment(s, port)
    while (cap.isOpened()):
        _, frame = cap.read()
        fs.udp_frame(frame)
    cap.release()
    cv2.destroyAllWindows()
    s.close()

def hello():
    print("hello, world")

if __name__ == "__main__":


    headers = {
        'content-type': 'application/json',
    }

    dataPlayload = '{"type": "playlist", "listType": "playlist", "id": "PLVlobiWMiFZBKf2Xy8d9f8Z0PJd41zSV9", "shuffle": "true", "loop": "true", "autoplay": "true"}'
    dataPlay = '{"command": "playVideo"}'
    dataPause = '{"command": "pauseVideo"}'

    # Set up UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = 12345
    fs = FrameSegment(s, port)

    cap = cv2.VideoCapture(0)

    threadudp = threading.Thread(target=sendFrame)
    threadudp.start()

    lasttime = time.time()
    t = 0

    thblynk = Threadblynk()
    thblynk.start()

    tvstate = Context()

    t = threading.Timer(300.0, tvstate.turnTV())

    threadfacedetection = threading.Thread(target=facedetection)
    threadfacedetection.start()
