import logging
import yaml
import aiohttp
import sys
import time
import os


with open("/root/.config/py_crust/config.yml", "r") as f:
    try:
        config = yaml.safe_load(f)
    except yaml.YAMLError:
        logging.error("Unable to load py_crust configuration")

DECIDE_VERSION = config['DECIDE_VERSION'].encode('utf-8')
REQ_ENDPOINT = config['REQ_ENDPOINT']
PUB_ENDPOINT = config['PUB_ENDPOINT']
TIMEOUT = config['TIMEOUT']
SLACK_HOOK = config['SLACK_HOOK']
LOCAL_LOG = config['LOCAL_LOG']
CONTACT_HOST = config['CONTACT_HOST']
HIVEMIND = config['HOST_ADDR']
IDENTITY = os.uname()[1]


async def lincoln(log, level=logging.DEBUG):
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    streamer = logging.StreamHandler(sys.stdout)
    streamer.setFormatter(formatter)
    filer = logging.FileHandler(log, mode='w')

    handlers = [filer, streamer] if LOCAL_LOG else [streamer]
    filer.setFormatter(formatter)
    logging.basicConfig(
        level=level,
        handlers=handlers
    )
    logging.debug(f"Logging to file {log}. Connecting to DecideAPI")
    # Trace is reserved for basic communication protocols of protobuf found in decrypt.py
    logging.PROTO = 5
    logging.addLevelName(logging.PROTO, 'PROTO')

    def proto(self, message, *args, **kws):
        if self.isEnabledFor(logging.PROTO):
            self._log(logging.PROTO, message, args, **kws)
    logging.Logger.proto = proto
    logging.__all__ += ['PROTO']
    # Dispatch is reserved for zmq operations found in relay.py
    logging.DISPATCH = 12
    logging.addLevelName(logging.DISPATCH, 'DISPATCH')

    def dispatch(self, message, *args, **kws):
        if self.isEnabledFor(logging.DISPATCH):
            self._log(logging.DISPATCH, message, args, **kws)
    logging.Logger.dispatch = dispatch
    logging.__all__ += ['DISPATCH']
    # State is reserved for state-machine operations found in process.py
    logging.STATE = 19
    logging.addLevelName(logging.STATE, 'STATE')

    def state(self, message, *args, **kws):
        if self.isEnabledFor(logging.STATE):
            self._log(logging.STATE, message, args, **kws)
    logging.Logger.state = state
    logging.__all__ += ['STATE']

    if CONTACT_HOST:
        async with aiohttp.ClientSession as session:
            try:
                async with session.get(urls=f"{HIVEMIND}/info/",
                                       ) as result:
                    logging.debug("Response received from Decide-Host")
                    reply = await result.json()
                    if result.status != 200:
                        logging.error('GET Result Error from getting Decide-Host info:', reply)
                    elif ('api_version' not in reply) or (reply.api_version is None):
                        logging.error('Unexpected reply from Decide-Host info:', reply)
                    else:
                        logging.info("Connected to Decide-Host.")
            except aiohttp.ClientConnectionError as e:
                logging.error('Could not contact Decide-Host:', str(e))
    else:
        logging.warning('Standalone Mode specified in config. Trials will not be logged')
    return


async def log_trial(msg: dict):
    if CONTACT_HOST:
        msg['addr'] = IDENTITY
        msg['time'] = time.time()
        async with aiohttp.ClientSession as session:
            try:
                async with session.post(url=f"{HIVEMIND}/trials/",
                                        json=msg,
                                        headers={'Content-Type': 'application/json'}
                                        ) as result:
                    if result.status != 200:
                        reply = await result.json()
                        logging.error('POST Result Error from contacting Decide-Host:', reply)
                    else:
                        logging.debug("Trial logged to DecideAPI.")
            except aiohttp.ClientConnectionError as e:
                logging.error('Could not contact Decide-Host:', str(e))
    return


async def slack(msg, usr=None):
    try:
        if isinstance(usr, list):
            users = "<" + "> <".join(usr) + ">"
            message = f"Hey {users}, {msg}"
        elif isinstance(usr, str):
            message = f"Hey <{usr}>, {msg}"
        else:
            message = f"{msg}. Praise Dan |('')|"
        slack_message = {'text': message}
        async with aiohttp.ClientSession as session:
            async with session.post(url=SLACK_HOOK,
                                    json=slack_message,
                                    headers={'Content-Type': 'application/json'}
                                    ) as result:
                reply = await result.json()
        logging.info(f"Slacked user, response: {reply}")
    except Exception as e:
        logging.warning(f"Slack Error: {e}")
    return


# This function maintains sanity
def peck_parse(phrase, mode):
    if mode in ['led', 'l', 'leds']:
        if 'left' in phrase:
            return 'peck_led_left'
        elif 'right' in phrase:
            return 'peck_led_right'
        elif 'center' in phrase:
            return 'peck_led_center'
    elif mode in ['response', 'r']:
        if 'left' in phrase:
            return 'peck_left'
        elif 'right' in phrase:
            return 'peck_right'
        elif 'center' in phrase:
            return 'peck_center'
