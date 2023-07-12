import asyncio
import logging
import yaml
import aiohttp
import sys
import time
import os

logger = logging.getLogger(__name__)

with open("/root/.config/py_crust/config.yml", "r") as f:
    try:
        config = yaml.safe_load(f)
    except yaml.YAMLError:
        logger.error("Unable to load py_crust configuration")

DECIDE_VERSION = config['DECIDE_VERSION'].encode('utf-8')
REQ_ENDPOINT = config['REQ_ENDPOINT']
PUB_ENDPOINT = config['PUB_ENDPOINT']
TIMEOUT = config['TIMEOUT']

SLACK_HOOK = config['SLACK_HOOK']
LOCAL_LOG = config['LOCAL_LOG']
CONTACT_HOST = config['CONTACT_HOST']
HIVEMIND = config['HOST_ADDR']
IDENTITY = os.uname()[1]


async def lincoln(log):
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    streamer = logging.StreamHandler(sys.stdout)
    streamer.setFormatter(formatter)
    if LOCAL_LOG:
        filer = logging.FileHandler(log, mode='w')
        filer.setFormatter(formatter)
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[filer, streamer]
        )
        logger.debug(f"Logging to file {log}. Connecting to DecideAPI")
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[streamer]
        )
        logger.debug(f"Not logging to file. Connecting to DecideAPI")

    if CONTACT_HOST:
        async with aiohttp.ClientSession as session:
            try:
                async with session.get(urls=f"{HIVEMIND}/info/",
                                       ) as result:
                    logger.debug("Response received from Decide-Host")
                    reply = await result.json()
                    if result.status != 200:
                        logger.error('GET Result Error from getting Decide-Host info:', reply)
                    elif ('api_version' not in reply) or (reply.api_version is None):
                        logger.error('Unexpected reply from Decide-Host info:', reply)
                    else:
                        logger.info("Connected to Decide-Host.")
            except aiohttp.ClientConnectionError as e:
                logger.error('Could not contact Decide-Host:', str(e))
    else:
        logger.warning('Standalone Mode specified in config. Trials will not be logged')
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
                        logger.error('POST Result Error from contacting Decide-Host:', reply)
                    else:
                        logger.debug("Trial logged to DecideAPI.")
            except aiohttp.ClientConnectionError as e:
                logger.error('Could not contact Decide-Host:', str(e))
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
        logger.info(f"Slacked user, response: {reply}")
    except Exception as e:
        logger.warning(f"Slack Error: {e}")
    return
