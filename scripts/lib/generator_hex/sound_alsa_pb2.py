# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: sound_alsa.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10sound_alsa.proto\"B\n\x07SaState\x12\x10\n\x08\x61udio_id\x18\x01 \x01(\t\x12\x10\n\x08playback\x18\x02 \x01(\x08\x12\x13\n\x0b\x66rame_count\x18\x03 \x01(\r\"G\n\x08SaParams\x12\x11\n\tconf_path\x18\x01 \x01(\t\x12\x13\n\x0b\x61udio_count\x18\x02 \x01(\r\x12\x13\n\x0bsample_rate\x18\x03 \x01(\rb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'sound_alsa_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _SASTATE._serialized_start=20
  _SASTATE._serialized_end=86
  _SAPARAMS._serialized_start=88
  _SAPARAMS._serialized_end=159
# @@protoc_insertion_point(module_scope)
