from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class SmState(_message.Message):
    __slots__ = ["switch", "on", "direction"]
    SWITCH_FIELD_NUMBER: _ClassVar[int]
    ON_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    switch: bool
    on: bool
    direction: bool
    def __init__(self, switch: bool = ..., on: bool = ..., direction: bool = ...) -> None: ...

class SmParams(_message.Message):
    __slots__ = ["timeout"]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    timeout: int
    def __init__(self, timeout: _Optional[int] = ...) -> None: ...
