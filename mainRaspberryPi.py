#!/usr/bin/env python

from __future__ import division
import cv2
import numpy as np
import socket
import struct
import math
import threading
import os
import subprocess
import sys
import time
import requests

class FrameSegment(object):
    """ 
    Object to break down image frame segment
    if the size of image exceed maximum datagram size 
    """
    MAX_DGRAM = 2**16
    MAX_IMAGE_DGRAM = MAX_DGRAM - 64 # extract 64 bytes in case UDP frame overflown
    def __init__(self, sock, port, addr="IPAdress"):
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

if __name__ == "__main__":
    headers = {
        'content-type': 'application/json',
    }

    dataPlayload = '{"type": "playlist", "listType": "playlist", "id": "PLVlobiWMiFZBKf2Xy8d9f8Z0PJd41zSV9", "shuffle": "true", "loop": "true", "autoplay": "true"}'
    dataPause = '{"command": "pauseVideo"}'

    # Set up UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = 12345
    fs = FrameSegment(s, port)

    cap = cv2.VideoCapture(0)

    thread_1 = threading.Thread(target=sendFrame)
    thread_1.start()
    state = 1
    youtubestate = 0
    lasttime = time.time()
    t = 0

    while True:
        data = b''
        data = s.recv(1024)

        if state:
            t += time.time() - lasttime
            print(t)
            if youtubestate == 0: 
                if t > 30:
                    requests.post('http://192.168.100.134:8080/api/module/youtube/youtubeload',
                                  headers=headers, data=dataPlayload)
                    youtubestate = 1
            if t > 300:
                if youtubestate:
                    requests.post('http://192.168.100.134:8080/api/module/youtube/youtubecontrol',
                                  headers=headers, data=dataPause)
                    youtubestate = 0
                os.system('echo "standby 0" | cec-client -s')
                state = 0
                t = 0

        
        if data == b'Face Detected':
            t = 0
            if state == 0:
                os.system('echo "on 0" | cec-client -s')
                state = 1

        lasttime = time.time()
