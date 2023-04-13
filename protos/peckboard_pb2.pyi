from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class LedState(_message.Message):
    __slots__ = ["led_state"]
    LED_STATE_FIELD_NUMBER: _ClassVar[int]
    led_state: str
    def __init__(self, led_state: _Optional[str] = ...) -> None: ...

class LedParams(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class KeyState(_message.Message):
    __slots__ = ["peck_left", "peck_center", "peck_right"]
    PECK_LEFT_FIELD_NUMBER: _ClassVar[int]
    PECK_CENTER_FIELD_NUMBER: _ClassVar[int]
    PECK_RIGHT_FIELD_NUMBER: _ClassVar[int]
    peck_left: bool
    peck_center: bool
    peck_right: bool
    def __init__(self, peck_left: bool = ..., peck_center: bool = ..., peck_right: bool = ...) -> None: ...

class KeyParams(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...
