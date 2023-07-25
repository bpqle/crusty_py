
### Protocol Buffer Setup:
This repo should come with pre-compiled _pb2.py files in ./protos, and therefore only requires the python implementation of protobuf (as denoted in `pyproject.toml`).

To compile the files yourself, you will also need the C++ `protoc` compiler, which can be tricky since
```
$ sudo apt install protobuf-compiler
```
can get you an outdated version that compiles .py files that can't be read by the python protobuf module.
The best guarantee is getting the most up-to-date (or v22.2 if you're working with the specific BeagleBone image this was designed for) release from https://github.com/protocolbuffers/protobuf/releases to compile these files.
You can download a pre-compiled `protoc` and place the files in the respective locations on the development machine (`/bin/protoc` goes to `/usr/bin/protoc` and `/include/*` goes in `/usr/local/include/`)

All proto files can be compiled at once using
```
 protoc -I ./protos --python_out=./lib/generator_hex ./protos/*.proto --pyi_out=./lib/generator_hex
```
This will generate google's vanilla `.py` files with `_pb2` in the name, as well as `.pyi` files in `./lib/generator_hex` for class reference.

### Deploying repo to connected beaglebone:
```
rsync -av -e ssh --exclude='.*' ./py_crust/ beagle-X:/root/py_crust/
```
### Configuration
Place a `config.yml` file in `/root/.config/py_crust/` on the beaglebone with the following fields:
```agsl
DECIDE_VERSION: // match decide-core version
REQ_ENDPOINT:
PUB_ENDPOINT: 
TIMEOUT: 100 //ms
SLACK_HOOK: // ping slack
LOCAL_LOG: true // log to file
CONTACT_HOST: true // connect to decide API
HIVEMIND: // host address
```

https://superuser.com/questions/610819/how-to-resize-img-file-created-with-dd