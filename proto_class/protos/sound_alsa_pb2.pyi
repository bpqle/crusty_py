from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SaState(_message.Message):
    __slots__ = ["audio_id", "playback", "elapsed"]
    class PlayBack(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        STOPPED: _ClassVar[SaState.PlayBack]
        PLAYING: _ClassVar[SaState.PlayBack]
        NEXT: _ClassVar[SaState.PlayBack]
    STOPPED: SaState.PlayBack
    PLAYING: SaState.PlayBack
    NEXT: SaState.PlayBack
    AUDIO_ID_FIELD_NUMBER: _ClassVar[int]
    PLAYBACK_FIELD_NUMBER: _ClassVar[int]
    ELAPSED_FIELD_NUMBER: _ClassVar[int]
    audio_id: str
    playback: SaState.PlayBack
    elapsed: _duration_pb2.Duration
    def __init__(self, audio_id: _Optional[str] = ..., playback: _Optional[_Union[SaState.PlayBack, str]] = ..., elapsed: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class SaParams(_message.Message):
    __slots__ = ["audio_dir", "audio_count"]
    AUDIO_DIR_FIELD_NUMBER: _ClassVar[int]
    AUDIO_COUNT_FIELD_NUMBER: _ClassVar[int]
    audio_dir: str
    audio_count: int
    def __init__(self, audio_dir: _Optional[str] = ..., audio_count: _Optional[int] = ...) -> None: ...
