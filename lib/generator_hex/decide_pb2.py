# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: decide.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0c\x64\x65\x63ide.proto\x12\x06\x64\x65\x63ide\x1a\x1bgoogle/protobuf/empty.proto\x1a\x19google/protobuf/any.proto\x1a\x1fgoogle/protobuf/timestamp.proto\"2\n\x0bStateChange\x12#\n\x05state\x18\x01 \x01(\x0b\x32\x14.google.protobuf.Any\";\n\x0f\x43omponentParams\x12(\n\nparameters\x18\x01 \x01(\x0b\x32\x14.google.protobuf.Any\"\x1c\n\x06\x43onfig\x12\x12\n\nidentifier\x18\x01 \x01(\t\"p\n\x05Reply\x12$\n\x02ok\x18\x02 \x01(\x0b\x32\x16.google.protobuf.EmptyH\x00\x12\x0f\n\x05\x65rror\x18\x03 \x01(\tH\x00\x12&\n\x06params\x18\x13 \x01(\x0b\x32\x14.google.protobuf.AnyH\x00\x42\x08\n\x06result\"T\n\x03Pub\x12(\n\x04time\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12#\n\x05state\x18\x02 \x01(\x0b\x32\x14.google.protobuf.Any2\xcc\x02\n\rDecideControl\x12\x31\n\x0b\x43hangeState\x12\x13.decide.StateChange\x1a\r.decide.Reply\x12\x33\n\nResetState\x12\x16.google.protobuf.Empty\x1a\r.decide.Reply\x12,\n\x0bRequestLock\x12\x0e.decide.Config\x1a\r.decide.Reply\x12\x34\n\x0bReleaseLock\x12\x16.google.protobuf.Empty\x1a\r.decide.Reply\x12\x37\n\rSetParameters\x12\x17.decide.ComponentParams\x1a\r.decide.Reply\x12\x36\n\rGetParameters\x12\x16.google.protobuf.Empty\x1a\r.decide.Replyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'decide_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _globals['_STATECHANGE']._serialized_start=113
  _globals['_STATECHANGE']._serialized_end=163
  _globals['_COMPONENTPARAMS']._serialized_start=165
  _globals['_COMPONENTPARAMS']._serialized_end=224
  _globals['_CONFIG']._serialized_start=226
  _globals['_CONFIG']._serialized_end=254
  _globals['_REPLY']._serialized_start=256
  _globals['_REPLY']._serialized_end=368
  _globals['_PUB']._serialized_start=370
  _globals['_PUB']._serialized_end=454
  _globals['_DECIDECONTROL']._serialized_start=457
  _globals['_DECIDECONTROL']._serialized_end=789
# @@protoc_insertion_point(module_scope)
