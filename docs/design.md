## General Principles

`py_crust` is designed to run alongside `decide-core` (also referred to as `decide-rs`), with each user-defined component that has a `State` and `Params`.
- `Params` indicate a experiment-specific variable that can be changed during runtime, but should ideally be set only once upon starting.
- `State` indicates the hardware component's runtime variables that can be influenced by the client, `decide-rs`, or the experimenter in the course of the trial.
The default components shipped with `py_crust` are:
- `house_light`: main LED used for simulating light cycle within a closed sound-box.
- `stepper_motor`: motor driver used for running food hopper.
- `peckboard`: comprised of left/center/right tri-color leds, and 3 keys which notify behavioral responses.
- `sound_alsa`: playback apparatus based on the alsa library.
On the `py_crust` client-side, each component is defined as an inner class of the `Components` class in `./lib/decrypt.py`. The inner class is essentially a wrapper around the protobuf classes found in `*_pb2.py`.
Collecting all components under the `Components` class allows for a unified method of component manipulation & message parsing, and consequently, abstraction from the process of communicating with the controller `decide-core`.

## Adding New Components:
1. Define the protobuf file under `protos/`  with `State` and `Params` messages. Make sure that `decide-core` has been compiled to include a driver for said component and has the driver enabled in its config file `/root/.config/decide/components.yml`.
 See [Deployment notes](deployment.md) on how to generate the referencable python classes from proto files.
2. Define the component subclass in `lib/decrypt.py`. Note that the `type_url` field has to be manually set to Google's default type_url convention for correct parsing.
3. If the component's pub message stream needs to be handled precisely, i.e. not purged blindly by the main state machine, you will need to specify a separate queue for it under `class Sauron` in `lib/dispatch.py`. An example of this is the `house-light` component.
4. Optionally, define high-level abstract methods for the component under `class Morgoth` in `lib/process.py`. Otherwise, component-specific requests can be formed through the `messenger` of `Morgoth`:
    ```
   asyncio.create_task(morgoth.messenger.command(
      request_type="ChangeState",
      component="component_name",
      body={'field':value}
   ```
   Pub messages from the component can be awaited and processed:
    ```
   asyncio.create_task(morgoth.scry(
        'component_name',
        condition=lambda pub: ('field' in pub) and (pub['field'] == value),
        failure=error_function,
        timeout=TIMEOUT
    ```

## Experiment Scripts:

