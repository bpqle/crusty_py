import logging
import asyncio, socket
import json
from .config import *

logger = logging.getLogger('main')


def make_response(info=None):
    if info is None:
        info = {'state': {}, 'params': {}}
    info.update({'script': __name__, 'device': IDENTITY})
    return info


async def set_server(snd_resp=make_response):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('lab', PORT_CTRL))
    server.listen(1)
    server.setblocking(False)
    loop = asyncio.get_running_loop()
    while True:
        client, address = await loop.sock_accept(server)
        logger.info("New Client Connected.")
        await handle_and_respond(client, address, snd_resp, loop)


async def handle_and_respond(client, address, snd_rsp, loop):
    request = ''
    while True:
        chunk = (await loop.sock_recv(client, 1024)).decode('utf-8')
        request += chunk
        if len(chunk) < 1024:
            break
    status, status_msg, url = parse_request(request)
    logger.debug(f"Request Url parsed as {url}")
    if url in {'/index.html', '/'}:
        response = snd_rsp()
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

