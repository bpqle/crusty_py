from lib.component_protos import decide_pb2 as dc_pb,\
    peckboard_pb2 as pb_pb, stepper_motor_pb2 as sm_pb, \
    sound_alsa_pb2 as sa_pb, house_light_pb2 as hl_pb
import google.protobuf.any_pb2 as _any
import logging

logger = logging.getLogger(__name__)


class Component:
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
            logger.error(f"Unrecognized/Unspecified Component Name {component}")

    async def from_any(self, any_msg: _any.Any):
        if any_msg.type_url == self.component.type_url:
            any_string = any_msg.value
            res = self.component.data.ParseFromString(any_string)
            logger.debug(f"{self.name} - {self.meta_type} - parsed Any message")
            return self.component.data
        else:
            logger.error(f" Mismatching type_urls, got {any_msg.type_url} expected {self.component.type_url}")

    async def to_any(self):
        any_msg = _any.Any()
        any_msg.type_url = self.component.type_url
        any_msg.Pack(self.component.data)
        logger.debug(f"{self.name} - {self.meta_type} - packed pb_Any.")
        return any_msg

    async def from_pub(self, msg):
        pub_msg = dc_pb.Pub()
        pub_msg.ParseFromString(msg)
        state_msg = await self.from_any(pub_msg.state)
        logger.debug(f"{self.name} - state-pub - message parsed")
        return pub_msg.time, state_msg

    async def to_req(self):
        if self.meta_type == 'state':
            req_msg = dc_pb.StateChange()
            req_msg.state.CopyFrom(await self.to_any())
            logger.debug(f"{self.name} - state request formed")
            return req_msg
        elif self.meta_type == 'param':
            req_msg = dc_pb.ComponentParams()
            req_msg.parameters.CopyFrom(await self.to_any())
            logger.debug(f"{self.name} - params request formed")
            return req_msg
        else:
            logger.error(f"Invalid meta-type {self.meta_type} for Component request to be formed")

    class HouseLight:

        def __init__(self, meta_type: str, data=None):
            if meta_type == "state":
                self.type_url = "type.googleapis.com/HlState"
                self.data = hl_pb.HlState(**data) if data else hl_pb.HlState()
            elif meta_type == "param":
                self.type_url = "type.googleapis.com/HlParams"
                self.data = hl_pb.HlParams(**data) if data else hl_pb.HlParams()

    class PeckKeys:

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "type.googleapis.com/KeyState"
                self.data = pb_pb.KeyState(**data) if data else pb_pb.KeyState()
            elif meta_type == "param":
                self.type_url = "type.googleapis.com/KeyParams"
                self.data = pb_pb.KeyParams()

    class PeckLed:

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "type.googleapis.com/LedState"
                self.data = pb_pb.LedState(**data) if data else pb_pb.LedState()
            elif meta_type == "param":
                self.type_url = "type.googleapis.com/LedParams"
                self.data = pb_pb.LedParams()

    class SoundAlsa:

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "type.googleapis.com/SaState"
                self.data = sa_pb.SaState(**data) if data else sa_pb.SaState()
            elif meta_type == "param":
                self.type_url = "type.googleapis.com/SaParams"
                self.data = sa_pb.SaParams(**data) if data else sa_pb.SaParams()

    class StepperMotor:

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "type.googleapis.com/SmState"
                self.data = sm_pb.SmState(**data) if data else sm_pb.SmState()
            elif meta_type == "param":
                self.type_url = "type.googleapis.com/SmParams"
                self.data = sm_pb.SmParams(**data) if data else sm_pb.SmParams()
