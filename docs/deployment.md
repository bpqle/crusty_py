This package should come with pre-compiled _pb2.py files in ./protos, and therefore only requires the python implementation of protobuf (as denoted in `pyproject.toml`).

To compile the files yourself, you will also need the C++ `protoc` compiler, which can be tricky since
```
$ sudo apt install protobuf-compiler
```
can get you an outdated version that compiles .py files that can't be read by the python protobuf module.
The best guarantee is getting the v22.2 release from https://github.com/protocolbuffers/protobuf/releases used to compile these files.
You can download a pre-compiled `protoc` and place the files in the respective locations (`/bin/protoc` goes to `/usr/bin/protoc` and `/include/*` goes in `/usr/local/include/`)

All proto files can be compiled at once using
```
 protoc -I ./protos --python_out=./lib/generator_hex ./protos/*.proto --pyi_out=./lib/generator_hex
```
This will generate google's vanilla `.py` files with `_pb2` in the name, as well as `.pyi` files in `./lib/generator_hex` for class reference.


```rsync -av -e ssh --exclude='.*' ./py_crust/ dimmabone:/root/py_crust/```
