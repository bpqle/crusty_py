from connect import Request
from components import Component
import asyncio
import logging
import zmq
import zmq.asyncio
import yaml
import urllib3
import traceback
import json

logger = logging.getLogger(__name__)


def global_config():
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


def slack(msg, usr=None):
    try:
        if isinstance(usr, list):
            users = "<"+"> <".join(usr)+">"
            message = f"Hey {users}, {msg}"
        elif isinstance(usr, str):
            message = f"Hey <{usr}>, {msg}"
        else:
            message = msg
        slack_message = {'text': message}
        http = urllib3.PoolManager()
        response = http.request('POST',
                                SLACK_HOOK,
                                body=json.dump(slack_message),
                                headers={'Content-Type': 'application`json'},
                                retries=False)
    except:
        traceback.print_exc()

    return
