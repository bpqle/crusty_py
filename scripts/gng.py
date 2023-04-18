import sys
import os
cpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib/'))
sys.path.insert(1, libpath)
sys.path.insert(1, cpath)

from lib.connect import Request, decide_poll
from lib.component_protos import Components
import asyncio
import time
import logging

components = ['house-light', 'stepper-motor',
              'peck-leds-left', 'peck-leds-center', 'peck-leds-right',
              'peck-keys', 'audio-playback']
