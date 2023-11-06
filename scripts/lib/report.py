import logging
import asyncio, socket
import json
from .config import *

logger = logging.getLogger('main')


def make_response(info=None):
    """
    generic response function
    """
    if info is None:
        info = {'state': {}, 'params': {}}
    info.update({'script': __name__, 'device': IDENTITY})
    return info


async def set_server(snd_resp=make_response, variables=None):
    """
    Set up a server responding to GET queries with html of exp state and parameters.
    Run alongside other async loop tasks.
    :param snd_resp: function
    :param variables: shallow copies of experiment variables, namely 'state' and 'params'.
    Formatted into dict.
    :return:
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', PORT_CTRL))
    server.listen(1)
    server.setblocking(False)
    loop = asyncio.get_running_loop()
    while True:
        client, address = await loop.sock_accept(server)
        logger.info("New Client Connected.")
        await handle_and_respond(client, address, snd_resp, variables, loop)


async def handle_and_respond(client, address, snd_rsp, variables, loop):
    """
    Simply parses the queries and responds only to GET.
    :param client: Along with address, returned objects from awaiting loop.sock_accept()
    :param address:
    :param snd_rsp: response generator
    :param variables: shallow copies of experiment variables, namely 'state' and 'params'
    :param loop: result of get_running_loop(), passed from set_server()
    :return:
    """
    request = ''
    while True:
        chunk = (await loop.sock_recv(client, 1024)).decode('utf-8')
        request += chunk
        if len(chunk) < 1024:
            break
    status, status_msg, url = parse_request(request)
    logger.debug(f"Request Url parsed as {url}")
    if url in {'/index.html', '/'}:
        response = snd_rsp(info=variables)
        payload = {'status': status, 'status_msg': status_msg, 'html': response}
        payload = json.dumps(payload, indent=4).encode('utf-8')
        await loop.sock_sendall(client, payload)
        logger.info("Response sent to client.")
        client.close()
        logger.debug("Client Closed")


def parse_request(reqstr):
    part_one, part_two = reqstr.split('\r\n\r\n')
    http_lines = part_one.split('\r\n')
    method, url, _ = http_lines[0].split(' ')
    if method != 'GET':
        status, status_msg = 405, 'Not allowed'
    else:
        logger.dispatch('GET Received')
        status, status_msg = 200, 'OK'
    return status, status_msg, url

