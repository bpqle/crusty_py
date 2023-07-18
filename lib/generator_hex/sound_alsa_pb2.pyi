from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class SaState(_message.Message):
    __slots__ = ["audio_id", "playback", "frame_count"]
    AUDIO_ID_FIELD_NUMBER: _ClassVar[int]
    PLAYBACK_FIELD_NUMBER: _ClassVar[int]
    FRAME_COUNT_FIELD_NUMBER: _ClassVar[int]
    audio_id: str
    playback: int
    frame_count: int
    def __init__(self, audio_id: _Optional[str] = ..., playback: _Optional[int] = ..., frame_count: _Optional[int] = ...) -> None: ...

class SaParams(_message.Message):
    __slots__ = ["audio_dir", "audio_count", "sample_rate"]
    AUDIO_DIR_FIELD_NUMBER: _ClassVar[int]
    AUDIO_COUNT_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    audio_dir: str
    audio_count: int
    sample_rate: int
    def __init__(self, audio_dir: _Optional[str] = ..., audio_count: _Optional[int] = ..., sample_rate: _Optional[int] = ...) -> None: ...
