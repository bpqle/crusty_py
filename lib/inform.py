import logging
import yaml
import aiohttp
import sys
import time
import os
import json

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
HOST_LOG = None
logger = logging.getLogger('main')


def lincoln(log, level='DEBUG'):

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    streamer = logging.StreamHandler(sys.stdout)
    streamer.setFormatter(formatter)
    logger.addHandler(streamer)
    if LOCAL_LOG:
        filer = logging.FileHandler(f"/root/py_crust/log/{log}", mode='w')
        filer.setFormatter(formatter)
        logger.addHandler(filer)

    logger.info(f"Logging to file {log}. Connecting to DecideAPI")
    # Proto is reserved for basic communication protocols of protobuf found in decrypt.py
    add_log_lvl('PROTO', 11, 'proto')
    # Dispatch is reserved for zmq operations found in dispatch.py
    add_log_lvl('DISPATCH', 12, 'dispatch')
    # State is reserved for state-machine operations found in process.py
    add_log_lvl('STATE', 13, 'state')
    logger.setLevel(level)


async def contact_host():
    global session
    if CONTACT_HOST:
        session = aiohttp.ClientSession()
        try:
            async with session.get(url=f"{HIVEMIND}/info/") as result:
                logger.dispatch("Response received from Decide-Host")
                reply = await result.json()
                if result.status != 200:
                    logger.error('GET Result Error from getting Decide-Host info:', reply)
                elif ('api_version' not in reply) or (reply['api_version'] is None):
                    logger.error('Unexpected reply from Decide-Host info:', reply)
                else:
                    logger.dispatch("Connected to Decide-Host.")
        except aiohttp.ClientConnectionError as e:
            logger.error('Could not contact Decide-Host:', str(e))
    else:
        logger.warning('Standalone Mode specified in config. Trials will not be logged')


async def post_host(msg: dict, target):
    """
    Send a POST request to the decide API specified in py_crust's config
    :param msg: dictionary of data. address and time will be automatically filled out
    :param target: 'trials' or 'events'
    :return:
    """
    global session
    if target not in ['trials', 'events']:
        logger.error(f"Specified type for decide API logging incorrect: {target}")
        raise
    if CONTACT_HOST:
        msg.update({
            'addr': IDENTITY,
            'time': time.time()
        })
        try:
            async with session.post(url=f"{HIVEMIND}/{target}/",
                                    json=msg,
                                    headers={'Content-Type': 'application/json'}
                                    ) as result:
                if result.status != 201:
                    reply = await result.json()
                    logger.error('POST Result Error from contacting Decide-Host:', reply.status)
                    with open(f'/root/py_crust/dropped_{target}.json', 'a') as file:
                        json.dump(msg, file)
                        f.write(os.linesep)
                else:
                    logger.dispatch("Data logged to DecideAPI.")
                    await post_dropped()
        except aiohttp.ClientConnectionError as e:
            logger.error('Could not contact Decide-Host:', str(e))
            with open(f'/root/py_crust/dropped_{target}.json', 'a') as file:
                json.dump(msg, file)
                file.write(os.linesep)


async def post_dropped():
    try:
        with open(f'/root/py_crust/dropped_trials.json', 'rb') as file:
            if file.read(2) != '[]':
                things = json.load(file)
                for data in things:
                    await post_host(data, 'trials')
                os.remove(f'dropped_trials.log')
    except FileNotFoundError:
        return


async def slack(msg, usr=None):
    global session
    if isinstance(usr, str):
        message = f"Hey <{usr}>, {msg}"
    else:
        message = f"{msg}. Praise Dan |('')|"
    slack_message = {'text': message}
    try:
        async with session.post(url=SLACK_HOOK,
                                json=slack_message,
                                headers={'Content-Type': 'application/json'}
                                ) as result:
            reply = await result.read()
        logger.info(f"Slacked {usr}, response: {reply}")
    except Exception as e:
        logger.warning(f"Slack Error: {e}")
    return


# The following function is taken from https://stackoverflow.com/questions/2183233
# Checkout module haggis for more information
def add_log_lvl(name, num, method_name):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.
    """
    if not method_name:
        method_name = name.lower()

    if hasattr(logging, name):
        raise AttributeError('{} already defined in logging module'.format(name))
    if hasattr(logging, method_name):
        raise AttributeError('{} already defined in logging module'.format(method_name))
    if hasattr(logging.getLoggerClass(), method_name):
        raise AttributeError('{} already defined in logger class'.format(method_name))

    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(num):
            self._log(num, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(num, message, *args, **kwargs)

    logging.addLevelName(num, name)
    setattr(logging, name, num)
    setattr(logging.getLoggerClass(), method_name, logForLevel)
    setattr(logging, method_name, logToRoot)


# This function maintains sanity
def peck_parse(phrase, mode):
    """
    Takes in a string containing location (left, right, center)
     and outputs a string that matches the method to be used
    :param phrase: string variable to be parsed
    :param mode: 'l' for led, 'r' for key/response
    :return:
    """
    if mode in ['led', 'l', 'leds']:
        if 'left' in phrase:
            return 'peck-leds-left'
        elif 'right' in phrase:
            return 'peck-leds-right'
        elif 'center' in phrase:
            return 'peck-leds-center'
    elif mode in ['response', 'r']:
        if 'left' in phrase:
            return 'peck_left'
        elif 'right' in phrase:
            return 'peck_right'
        elif 'center' in phrase:
            return 'peck_center'
