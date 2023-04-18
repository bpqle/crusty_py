any_pb2.Any() has 2 fields: type_url and value. It also has its own DESCRIPTOR, but as expected, not the same DESCRIPTOR as the message packed within value.
To see if the message class you are trying to unpack to is valid, you must call any_msg.Is(message.DESCRIPTOR). This returns True or False.
Comparing type_url may pass, but the DESCRIPTOR check can return false.
We won't know how DESCRIPTOR comparison fails, so we must acquire the field names of the message's DESCRIPTOR with
fields = message.DESCRIPTOR.fields_by_name.keys()
And at the same time, Any() has a method HasField() in it, so ideally we should be able to do:
field_check = [any_msg.HasField(f) for f in fields]
But instead of getting a boolean result (like Is()), HasField() raises a ValueError when the field is not in there.

Unpacking involves theses steps:
```agsl
msg = pb_file.MessageClass()
any_msg.Unpack(msg)
return msg
```
However, Unpacking can fail silently by returning false