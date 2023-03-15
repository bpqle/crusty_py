import protos.house_light_pb2 as hl_proto
import protos.peckboard_pb2 as pb_proto
import protos.sound_alsa_pb2 as sa_proto
import protos.stepper_motor_pb2 as sm_proto

import asyncio

class HouseLight:
    def __init__(self):
        self.switch = True
        self.brightness = 0
        self.ephemera = False
        self.daytime = False
    def startup_ephemera(self):
        self.ephemera = False
        self.switch = False

class PeckBoard:
    def __init__(self):
        something
    def cue_light(self, position, state):
        something
    async def peck_check(self):
        return position

class StepperMotor:
    def __init__(self):s
        something
    def run_motor(self, duration):
        something

class SoundAlsa:
    def __init__(self):
        something
    def shuffle:
    def play_next: