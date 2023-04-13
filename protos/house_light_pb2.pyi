from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class HlState(_message.Message):
    __slots__ = ["manual", "ephemera", "brightness", "daytime"]
    MANUAL_FIELD_NUMBER: _ClassVar[int]
    EPHEMERA_FIELD_NUMBER: _ClassVar[int]
    BRIGHTNESS_FIELD_NUMBER: _ClassVar[int]
    DAYTIME_FIELD_NUMBER: _ClassVar[int]
    manual: bool
    ephemera: bool
    brightness: int
    daytime: bool
    def __init__(self, manual: bool = ..., ephemera: bool = ..., brightness: _Optional[int] = ..., daytime: bool = ...) -> None: ...

class HlParams(_message.Message):
    __slots__ = ["clock_interval"]
    CLOCK_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    clock_interval: int
    def __init__(self, clock_interval: _Optional[int] = ...) -> None: ...
