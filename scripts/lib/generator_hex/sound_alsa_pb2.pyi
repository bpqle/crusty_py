from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class SaParams(_message.Message):
    __slots__ = ["audio_count", "conf_path", "sample_rate"]
    AUDIO_COUNT_FIELD_NUMBER: _ClassVar[int]
    CONF_PATH_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    audio_count: int
    conf_path: str
    sample_rate: int
    def __init__(self, conf_path: _Optional[str] = ..., audio_count: _Optional[int] = ..., sample_rate: _Optional[int] = ...) -> None: ...

class SaState(_message.Message):
    __slots__ = ["audio_id", "frame_count", "playback"]
    AUDIO_ID_FIELD_NUMBER: _ClassVar[int]
    FRAME_COUNT_FIELD_NUMBER: _ClassVar[int]
    PLAYBACK_FIELD_NUMBER: _ClassVar[int]
    audio_id: str
    frame_count: int
    playback: bool
    def __init__(self, audio_id: _Optional[str] = ..., playback: bool = ..., frame_count: _Optional[int] = ...) -> None: ...
