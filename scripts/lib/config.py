import yaml
import logging
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
HOST_LOG = None