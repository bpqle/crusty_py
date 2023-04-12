import decide_pb2 as dc_pb
import house_light_pb2 as hl_pb
import peckboard_pb2 as pb_pb
import sound_alsa_pb2 as sa_pb
import stepper_motor_pb2 as sm_pb
import google.protobuf.any_pb2 as _any

import logging


class Components:
    def __init__(self, meta_type: str, component=None, data=None):
        self.name = component
        self.meta_type = meta_type
        if component == "house-light":
            self.component = self.HouseLight(meta_type, data)
        elif component in ["peck-leds-left", b"peck-leds-right", b"peck-leds-center"]:
            self.component = self.PeckLed(meta_type, data)
        elif component == "stepper-motor":
            self.component = self.StepperMotor(meta_type, data)
        elif component == "peck-keys":
            self.component = self.PeckKeys(meta_type, data)
        elif component == "sound-alsa":
            self.component = self.SoundAlsa(meta_type, data)
        else:
            print(f"Error: Unrecognized Component {component}")

    def from_any(self, any_msg: _any.Any):
        decoded_msg = self.component.from_any(any_msg)
        return decoded_msg

    def to_any(self):
        encoded_msg = self.component.to_any()
        return encoded_msg

    def from_pub(self, msg):
        pub_msg = dc_pb.Pub()
        pub_msg.ParseFromString(msg)
        any_state = _any.Any()
        any_state.CopyFrom(pub_msg.state)
        state_msg = self.from_any(any_state)
        return pub_msg.time, state_msg

    def to_req(self):
        if self.meta_type == 'state':
            req_msg = dc_pb.StateChange()
            req_msg.state.CopyFrom(self.to_any())
            return req_msg
        elif self.meta_type == 'param':
            req_msg = dc_pb.ComponentParams()
            print(type(req_msg.parameters))
            req_msg.parameters.CopyFrom(self.to_any())
            return req_msg
        else:
            print(f"Error: invalid meta-type {self.meta_type} for Component request to be formed")

    class HouseLight:
        class State:
            def __init__(self, manual=False, ephemera=False, brightness=50, daytime=True):
                self.pb_obj = hl_pb.HlState()
                self.pb_obj.manual = manual
                self.pb_obj.ephemera = ephemera
                self.pb_obj.brightness = brightness
                self.pb_obj.daytime = daytime

        class Param:
            def __init__(self, clock_interval=3000):
                self.pb_obj = hl_pb.HlParams()
                self.pb_obj.clock_interval = clock_interval

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "melizalab.org/proto/house_light_state"
                if data is None:
                    self.data = self.State()
                else:
                    print(data)
                    self.data = self.State(**data)
            elif meta_type == "param":
                self.type_url = "melizalab.org/proto/house_light_params"
                if data is None:
                    self.data = self.Param()
                else:
                    self.data = self.Param(**data)

        def from_any(self, any_msg):
            any_msg.Unpack(self.data.pb_obj)
            return self.data.pb_obj

        def to_any(self):
            any_msg = _any.Any()
            any_msg.Pack(self.data.pb_obj)
            any_msg.type_url = self.type_url
            return any_msg

    class PeckKeys:
        class State:
            def __init__(self, peck_left=False, peck_center=False, peck_right=False):
                self.pb_obj = pb_pb.KeyState()
                self.pb_obj.peck_left = peck_left
                self.pb_obj.peck_center = peck_center
                self.pb_obj.peck_right = peck_right

        class Param:
            def __init__(self):
                self.pb_obj = pb_pb.KeyParams()

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "melizalab.org/proto/key_state"
                if data is None:
                    self.data = self.State()
                else:
                    self.data = self.State(**data)
            elif meta_type == "param":
                self.type_url = "melizalab.org/proto/key_params"
                self.data = self.Param()

        def from_any(self, any_msg):
            any_msg.Unpack(self.data.pb_obj)
            return self.data.pb_obj

        def to_any(self):
            any_msg = _any.Any()
            any_msg.Pack(self.data.pb_obj)
            any_msg.type_url = self.type_url
            return any_msg

    class PeckLed:
        class State:
            def __init__(self, led_state="off"):
                self.pb_obj = pb_pb.LedState()
                self.pb_obj.led_state = led_state

        class Param:
            def __init__(self):
                self.pb_obj = pb_pb.LedParams()

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "melizalab.org/proto/led_state"
                if data is None:
                    self.data = self.State()
                else:
                    self.data = self.State(**data)
            elif meta_type == "param":
                self.type_url = "melizalab.org/proto/led_params"
                self.data = self.Param()

        def from_any(self, any_msg):
            any_msg.Unpack(self.data.pb_obj)
            return self.data.pb_obj

        def to_any(self):
            any_msg = _any.Any()
            any_msg.Pack(self.data.pb_obj)
            any_msg.type_url = self.type_url
            return any_msg

    class SoundAlsa:
        class State:
            def __init__(self, audio_id=None, playback="STOPPED", elapsed=0):
                self.pb_obj = sa_pb.SaState()
                self.pb_obj.audio_id = audio_id
                self.pb_obj.playback = playback
                self.pb_obj.elapsed = elapsed

        class Param:
            def __init__(self, audio_dir=None, audio_count=0):
                self.pb_obj = sa_pb.SaParams()
                self.pb_obj.audio_dir = audio_dir
                self.pb_obj.audio_count = audio_count

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "melizalab.org/proto/sound_alsa_state"
                if data is None:
                    self.data = self.State()
                else:
                    self.data = self.State(**data)
            elif meta_type == "param":
                self.type_url = "melizalab.org/proto/sound_alsa_params"
                if data is None:
                    self.data = self.Param()
                else:
                    self.data = self.Param(**data)

        def from_any(self, any_msg):
            any_msg.Unpack(self.data.pb_obj)
            return self.data.pb_obj

        def to_any(self):
            any_msg = _any.Any()
            any_msg.Pack(self.data.pb_obj)
            any_msg.type_url = self.type_url
            return any_msg

    class StepperMotor:
        class State:
            def __init__(self, switch=False, on=False, direction=False):
                self.pb_obj = sm_pb.SmState()
                self.pb_obj.switch = switch
                self.pb_obj.on = on
                self.pb_obj.direction = direction

        class Param:
            def __init__(self, timeout=0):
                self.pb_obj = sm_pb.SmParams()
                self.pb_obj.timeout = timeout

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "melizalab.org/proto/stepper_motor_state"
                if data is None:
                    self.data = self.State()
                else:
                    self.data = self.State(**data)
            elif meta_type == "param":
                self.type_url = "melizalab.org/proto/stepper_motor_params"
                if data is None:
                    self.data = self.Param()
                else:
                    self.data = self.Param(**data)

        def from_any(self, any_msg):
            any_msg.Unpack(self.data.pb_obj)
            return self.data.pb_obj

        def to_any(self):
            any_msg = _any.Any()
            any_msg.Pack(self.data.pb_obj)
            any_msg.type_url = self.type_url
            return any_msg
