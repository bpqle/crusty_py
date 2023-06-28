from lib.component_protos import decide as dc_pb,\
    peckboard as pb_pb, stepper_motor as sm_pb, \
    sound_alsa as sa_pb, house_light as hl_pb
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
            res = self.component.data.parse(any_string)
            logger.debug(f"{self.name} - {self.meta_type} - parsed Any message")
            return res
        else:
            logger.error(f" Mismatching type_urls")

    async def to_any(self):
        any_msg = _any.Any()
        any_msg.Pack(self.component.data)
        any_msg.type_url = self.component.type_url
        logger.debug(f"{self.name} - {self.meta_type} - packed pb_Any.")
        return any_msg

    async def from_pub(self, msg):
        pub_msg = dc_pb.Pub()
        pub_msg.parse(msg)
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
                self.type_url = "hl_state"
                if data is None:
                    self.data = hl_pb.HlState()
                else:
                    self.data = hl_pb.HlState(**data)
            elif meta_type == "param":
                self.type_url = "hl_params"
                if data is None:
                    self.data = hl_pb.HlParams()
                else:
                    self.data = hl_pb.HlParams(**data)

    class PeckKeys:

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "key_state"
                if data is None:
                    self.data = pb_pb.KeyState()
                else:
                    self.data = pb_pb.KeyState(**data)
            elif meta_type == "param":
                self.type_url = "key_params"
                self.data = pb_pb.KeyParams()

    class PeckLed:

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "led_state"
                if data is None:
                    self.data = pb_pb.LedState()
                else:
                    self.data = pb_pb.LedState(**data)
            elif meta_type == "param":
                self.type_url = "led_params"
                self.data = pb_pb.LedParams()

    class SoundAlsa:

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "sa_state"
                if data is None:
                    self.data = sa_pb.SaState()
                else:
                    self.data = sa_pb.SaState(**data)
            elif meta_type == "param":
                self.type_url = "sa_params"
                if data is None:
                    self.data = sa_pb.SaParams()
                else:
                    self.data = sa_pb.SaParams(**data)

    class StepperMotor:

        def __init__(self, meta_type: str, data=None):
            self.meta_type = meta_type
            if meta_type == "state":
                self.type_url = "sm_state"
                if data is None:
                    self.data = sm_pb.SmState()
                else:
                    self.data = sm_pb.SmState(**data)
            elif meta_type == "param":
                self.type_url = "sm_params"
                if data is None:
                    self.data = sm_pb.SmParams()
                else:
                    self.data = sm_pb.SmParams(**data)
