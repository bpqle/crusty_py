from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class SmParams(_message.Message):
    __slots__ = ["timeout"]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    timeout: int
    def __init__(self, timeout: _Optional[int] = ...) -> None: ...

class SmState(_message.Message):
    __slots__ = ["direction", "running"]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    RUNNING_FIELD_NUMBER: _ClassVar[int]
    direction: bool
    running: bool
    def __init__(self, running: bool = ..., direction: bool = ...) -> None: ...
