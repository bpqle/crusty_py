from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class HlParams(_message.Message):
    __slots__ = ["clock_interval"]
    CLOCK_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    clock_interval: int
    def __init__(self, clock_interval: _Optional[int] = ...) -> None: ...

class HlState(_message.Message):
    __slots__ = ["brightness", "daytime", "dyson", "manual"]
    BRIGHTNESS_FIELD_NUMBER: _ClassVar[int]
    DAYTIME_FIELD_NUMBER: _ClassVar[int]
    DYSON_FIELD_NUMBER: _ClassVar[int]
    MANUAL_FIELD_NUMBER: _ClassVar[int]
    brightness: int
    daytime: bool
    dyson: bool
    manual: bool
    def __init__(self, manual: bool = ..., dyson: bool = ..., brightness: _Optional[int] = ..., daytime: bool = ...) -> None: ...
