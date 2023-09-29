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
                    try:
                        reply = await result.json(content_type=None)
                    except json.decoder.JSONDecodeError as e:
                        logger.error(f"JSON Decode Error from parsing HOST response {result.status}: {result}")
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




