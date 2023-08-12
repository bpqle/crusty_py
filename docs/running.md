## HI
`py_crust` is designed to run alongside `decide-rs`, with each user-defined component that has a `State` and `Params`. 
 - `Params` indicate a experiment-specific variable that can be changed during runtime, but should ideally be set only once upon starting.
 - `State` indicates the hardware component's runtime variables that can be influenced by the client, `decide-rs`, or the experimenter in the course of the trial.

On the `py_crust` client-side, each component is defined as an inner class of the `Components` class in `./lib/decrypt.py`. The inner class is essentially a wrapper around the protobuf classes found in `*_pb2.py`.
Collecting all components under the `Components` class allows for a unified method of component manipulation & message parsing, and consequently, abstraction from the process of communicating with the controller `decide-core`.

