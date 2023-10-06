import logging
import aiohttp
import requests
import time
import os
import json
from .config import *
logger = logging.getLogger('main')


async def contact_host():
    global session
    if CONTACT_HOST:
        session = aiohttp.ClientSession()
        try:
            async with session.get(url=f"{HIVEMIND}/info/") as result:
                logger.dispatch("Response received from Decide-Host")
                reply = await result.json()
                if not result.ok:
                    logger.error(f'Error {result.status} from getting Decide-Host info:', reply)
                elif ('api_version' not in reply) or (reply['api_version'] is None):
                    logger.error('Unexpected reply from Decide-Host info:', reply)
                else:
                    logger.dispatch("Connected to Decide-Host.")
        except aiohttp.ClientConnectionError as e:
            logger.error('Could not contact Decide-Host. Is it running?', str(e))
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
                if not result.ok:
                    reply = await result.text()
                    logger.error(f'Error {result.status} from submitting data to Decide-Host:', reply)
                    log_dropped(target, msg)
                else:
                    logger.dispatch("Data logged to DecideAPI.")
                    await post_dropped(target)
        except aiohttp.ClientConnectionError as e:
            logger.error('Could not contact Decide-Host:', str(e))
            log_dropped(target, msg)


def log_dropped(target, msg):
    try:
        with open(f'/root/py_crust/dropped_{target}.json', 'r+') as file:
            current_dropped = json.load(file)
    except json.decoder.JSONDecodeError as e:  # empty file
        logger.debug(f"Dropped_{target} JSON Storage Does not exist yet. Creating file.")
        current_dropped = []
    current_dropped.append(msg)
    with open(f'/root/py_crust/dropped_{target}.json', 'w+') as file:
        json.dump(current_dropped, file, indent=4, separators=(',', ': '))


async def post_dropped(target):
    try:
        with open(f'/root/py_crust/dropped_{target}.json', 'r') as file:
            data = json.load(file)
            for d in data:
                await post_host(d, target)
        os.remove(f'/root/py_crust/dropped_{target}.json')
    except FileNotFoundError:
        return


def slack(msg, usr=None):
    if isinstance(usr, str):
        message = f"Hey <{usr}>, {msg}"
    else:
        message = f"{msg}. Praise Dan ('')"
    slack_message = {'text': message}
    try:
        with requests.post(
            SLACK_HOOK,
            json=slack_message,
            headers={'Content-Type': 'application/json'}
        ) as response:
            logger.info(f"Slacked {usr}, response: {response.content}")
    except Exception as e:
        logger.warning(f"Slack Error: {e}")
    return




