This package should come with pre-compiled _pb2.py files in ./protos, and therefore only requires the python implementation of protobuf (as denoted in `pyproject.toml`).

To compile the files yourself, you will also need the C++ `protoc` compiler, which can be tricky since
```
$ sudo apt install protobuf-compiler
```
can get you an outdated version that compiles .py files that can't be read by the python protobuf module.
The best guarantee is getting the v22.2 release from https://github.com/protocolbuffers/protobuf/releases used to compile these files.
You can download a pre-compiled `protoc` and place the files in the respective locations (`/bin/protoc` goes to `/usr/bin/protoc` and `/include/*` goes in `/usr/local/include/`)

usually
All proto files can be compiled at once using
protoc -I=./ --python_out=./ ./*.proto

However, compiler will fail if there are identically named objects in different .proto files being compiled simultaneously.
You can either change the `State` and `Param` in each proto file to a unique name, or compile each file individually:

protoc -I=./ --python_out=./ house_light.proto

