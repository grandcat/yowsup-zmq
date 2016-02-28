#!/usr/bin/env python3
import asyncio
import zmq
import zmq.asyncio

ctx = zmq.asyncio.Context()
loop = zmq.asyncio.ZMQEventLoop()
asyncio.set_event_loop(loop)

@asyncio.coroutine
def recv_and_process():
    sock = ctx.socket(zmq.REQ)
    sock.connect("tcp://127.0.0.1:%s" % 5555)
    print("Waiting...")

    # Create group
    yield from sock.send_json({"cmd": "group_create",
                               "participants": ["49176123456","49175654321"],
                               "subject": "Lets discuss about nerdy topics"})
    # Wait for result and print it
    result = yield from sock.recv_multipart()
    print(result[0].decode())

loop.run_until_complete(recv_and_process())