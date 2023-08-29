## DEVELOPMENT SIDE

Let it first be understood that the developer of this package does not take pleasure in using `poetry`, `protocol-buffer`, `python`, asynchronous `python`, or programming in general.

`pyproject.toml` will provide information on which specific python version and module versions that needs to be used for beagle-bone development. 
At the time of writing, the `python` version on the beagle-bone Debian 11 image is at `3.9.2`, which will be older than most up-to-date development machines.

`pyenv` is recommended by `poetry` for `python` version control. Installation instruction for `pyenv` can be found at https://github.com/pyenv/pyenv#installation.
 Once `pyenv` is installed, you will also need to run
```commandline
sudo apt-get install build-essential zlib1g-dev libffi-dev libssl-dev libbz2-dev libreadline-dev libsqlite3-dev liblzma-dev
```
to succesfully install any new `python`version, such as:
```commandline
pyenv install 3.9.2
pyenv local 3.9.2  
```
Following installation of `python`, if you would like to use `poetry`, run `which python3` and pipe the resulting location to 
```poetry env use [path]``` to be able to run `poetry install`

#### Notes:
 Some 'pythonic' and/or required syntax will change if `python` is fast-forwarded, and these should be documented in case of upgrade needed:
1. `asyncio.wait_for(async_func, timeout)` changes in 3.10, and `try: async with asyncio.timeout(time): [do async task]` is introduced in 3.11. Not necessary to change over to the latter syntax, though it allows for more flexible code.
2. It is highly likely that `protocol-buffer` code will change with time to even further obfuscate itself. There exists the plugin `betterproto` that, while introducing a [much better python-to-production system](https://github.com/danielgtaylor/python-betterproto#motivation), is lacking in support for predefined types like `Any()` or `Enum` in protocol buffer.

## BEAGLEBONE SIDE
### Useful Links:
https://superuser.com/questions/610819/how-to-resize-img-file-created-with-dd