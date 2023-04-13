from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StateChange(_message.Message):
    __slots__ = ["state"]
    STATE_FIELD_NUMBER: _ClassVar[int]
    state: _any_pb2.Any
    def __init__(self, state: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class ComponentParams(_message.Message):
    __slots__ = ["parameters"]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    parameters: _any_pb2.Any
    def __init__(self, parameters: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class Config(_message.Message):
    __slots__ = ["identifier"]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    identifier: str
    def __init__(self, identifier: _Optional[str] = ...) -> None: ...

class Reply(_message.Message):
    __slots__ = ["ok", "error", "params"]
    OK_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    ok: _empty_pb2.Empty
    error: str
    params: _any_pb2.Any
    def __init__(self, ok: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ..., error: _Optional[str] = ..., params: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class Pub(_message.Message):
    __slots__ = ["time", "state"]
    TIME_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    time: _timestamp_pb2.Timestamp
    state: _any_pb2.Any
    def __init__(self, time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., state: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
