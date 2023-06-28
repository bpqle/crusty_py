import asyncio
import logging
import yaml
import json
import aiohttp

logger = logging.getLogger(__name__)


async def global_config():
    with open("~/.config/py_crust/config.json", "r") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError:
            logger.error("Unable to load py_crust configuration")
    globals()['DECIDE_VERSION'] = config['DECIDE_VERSION'].encode('utf-8')
    globals()['REQ_ENDPOINT'] = config['REQ_ENDPOINT']
    globals()['PUB_ENDPOINT'] = config['PUB_ENDPOINT']
    globals()['TIMEOUT'] = config['TIMEOUT']
    globals()['SLACK_HOOK'] = config['SLACK_HOOK']
    return


def log_trial(state):
    return


async def slack(msg, usr=None):
    try:
        if isinstance(usr, list):
            users = "<"+"> <".join(usr)+">"
            message = f"Hey {users}, {msg}"
        elif isinstance(usr, str):
            message = f"Hey <{usr}>, {msg}"
        else:
            message = msg
        slack_message = {'text': message}
        async with aiohttp.ClientSession as session:
            async with session.post(url=SLACK_HOOK,
                                    json=slack_message,
                                    headers={'Content-Type': 'application`json'}
                                    ) as rep:
                reply = await rep.json()
    except Exception as e:
        logger.error(f"Slack Error: {e}")

    logger.info(f"Slacked user, response: {reply}")
    return
