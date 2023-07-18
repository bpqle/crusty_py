### DEVELOPMENT SIDE

Let it first be understood that the developer of this package does not take pleasure of using `poetry`, `protocol-buffer`, any asynchronous programming in `python`, or `python` in general.

`pyproject.toml` will provide information on which specific python version and module versions that needs to be used for beagle-bone development. 
At the time of writing, `python` is at `3.9.2`, which will be older than most up-to-date development machine.

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

### BEAGLEBONE SIDE
