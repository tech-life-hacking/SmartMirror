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
RaspberryPiIPAdress = 'YourRaspberryPiIPAdress'

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
        requests.post('http://'+RaspberryPiIPAdress+':8080/api/module/youtube/youtubeload',
                      headers=headers, data=dataPlayload0)

# register handler for virtual pin V3 write event


@blynk.handle_event('write V3')
def write_virtual_pin_handler(pin, value):
    if value == ['1']:
        requests.post('http://'+RaspberryPiIPAdress+':8080/api/module/youtube/youtubeload',
                      headers=headers, data=dataPlayload1)

# register handler for virtual pin V4 write event


@blynk.handle_event('write V4')
def write_virtual_pin_handler(pin, value):
    if value == ['1']:
        requests.post('http://'+RaspberryPiIPAdress+':8080/api/module/youtube/youtubecontrol',
                      headers=headers, data=dataPause)


class TVState():
    def turnTV(self):
        raise NotImplementedError("turnTV is abstractmethod")

    def changingtimer(self):
        raise NotImplementedError("changingtimer is abstractmethod")

    def turnYouTube(self):
        raise NotImplementedError("turnYouTube is abstractmethod")


class TVON(TVState):
    def turnTV(self):
        requests.post('http://'+RaspberryPiIPAdress+':8080/api/module/youtube/youtubecontrol',
                      headers=headers, data=dataPause)
        os.system('echo "standby 0" | cec-client -s')
        tvstate.change_state("tvon2off")

    def changingtimer(self):
        pass

    def turnYouTube(self):
        youtubestate.turnYouTube()
        youtubestate.changingtimer()


class TVON2OFF(TVState):
    def turnTV(self):
        pass

    def changingtimer(self):
        time.sleep(5)
        tvstate.change_state("tvoff")

    def turnYouTube(self):
        pass


class TVOFF(TVState):
    def turnTV(self):
        requests.post('http://'+RaspberryPiIPAdress+':8080/api/module/youtube/youtubecontrol',
                      headers=headers, data=dataPlay)
        os.system('echo "on 0" | cec-client -s')
        tvstate.change_state("tvoff2on")

    def changingtimer(self):
        pass

    def turnYouTube(self):
        pass


class TVOFF2ON(TVState):
    def turnTV(self):
        pass

    def changingtimer(self):
        time.sleep(10)
        tvstate.change_state("tvon")

    def turnYouTube(self):
        pass


class TVContext:
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
            raise ValueError("change_state method must be in {}".format(
                ["tvon", "tvon2off", "tvoff", "tvoff2on"]))

    def turnTV(self):
        self.state.turnTV()

    def changingtimer(self):
        self.state.changingtimer()

    def turnYouTube(self):
        self.state.turnYouTube()


class YouTubeState():
    def turnYouTube(self):
        raise NotImplementedError("turnYouTube is abstractmethod")

    def changingtimer(self):
        raise NotImplementedError("changingtimer is abstractmethod")


class YouTubeON(YouTubeState):
    def turnYouTube(self):
        requests.post('http://'+RaspberryPiIPAdress+':8080/api/module/youtube/youtubecontrol',
                      headers=headers, data=dataPause)
        youtubestate.change_state("youtubeon2off")

    def changingtimer(self):
        pass


class YouTubeON2OFF(YouTubeState):
    def turnYouTube(self):
        pass

    def changingtimer(self):
        time.sleep(3)
        youtubestate.change_state("youtubeoff")


class YouTubeOFF(YouTubeState):
    def turnYouTube(self):
        requests.post('http://'+RaspberryPiIPAdress+':8080/api/module/youtube/youtubecontrol',
                      headers=headers, data=dataPlay)
        youtubestate.change_state("youtubeoff2on")

    def changingtimer(self):
        pass


class YouTubeOFF2ON(YouTubeState):
    def turnYouTube(self):
        pass

    def changingtimer(self):
        time.sleep(3)
        youtubestate.change_state("youtubeon")


class YouTubeContext:
    def __init__(self):
        self.youtubeon = YouTubeON()
        self.youtubeon2off = YouTubeON2OFF()
        self.youtubeoff = YouTubeOFF()
        self.youtubeoff2on = YouTubeOFF2ON()
        self.state = self.youtubeoff

    def change_state(self, switchsignal):
        if switchsignal == "youtubeon":
            self.state = self.youtubeon
        elif switchsignal == "youtubeon2off":
            self.state = self.youtubeon2off
        elif switchsignal == "youtubeoff":
            self.state = self.youtubeoff
        elif switchsignal == "youtubeoff2on":
            self.state = self.youtubeoff2on
        else:
            raise ValueError("change_state method must be in {}".format(
                ["youtubeon", "youtubeon2off", "youtubeoff", "youtubeoff2on"]))

    def turnYouTube(self):
        self.state.turnYouTube()

    def changingtimer(self):
        self.state.changingtimer()


if __name__ == "__main__":

    headers = {
        'content-type': 'application/json',
    }

    dataPlayload0 = '{"type": "playlist", "listType": "playlist", "id": "PLVlobiWMiFZBKf2Xy8d9f8Z0PJd41zSV9", "shuffle": "true", "loop": "true", "autoplay": "true"}'
    dataPlayload1 = '{"type": "playlist", "listType": "playlist", "id": "PLVlobiWMiFZB-WzErl14EvUQ-OE7E3iTp", "shuffle": "true", "loop": "true", "autoplay": "true"}'
    dataPlay = '{"command": "playVideo"}'
    dataPause = '{"command": "pauseVideo"}'

    thblynk = Threadblynk()
    thblynk.start()

    tvstate = TVContext()
    youtubestate = YouTubeContext()

    # t = threading.Timer(300.0, tvstate.turnTV())

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((''+RaspberryPiIPAdress+'', 50007))
        s.listen(1)
        while True:
            conn, addr = s.accept()
            with conn:
                while True:
                    data = b''
                    data = conn.recv(1024)
                    if data == b'TurnYouTube':
                        tvstate.turnYouTube()
                    elif data == b'TurnTV':
                        tvstate.turnTV()
                        tvstate.changingtimer()
                    else:
                        pass
