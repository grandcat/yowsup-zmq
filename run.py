#!/usr/bin/env python3
from zmqlayer import ZmqBrokerLayer

from yowsup.layers.auth                        import AuthError
from yowsup.layers.network                     import YowNetworkLayer
from yowsup.layers import YowLayerEvent, YowParallelLayer
from yowsup.stacks import YowStackBuilder

import sys
import configparser


if __name__==  "__main__":
    stackBuilder = YowStackBuilder()

    stack = stackBuilder\
        .pushDefaultLayers(True)\
        .push(ZmqBrokerLayer)\
        .build()

    # Load credentials
    config = configparser.ConfigParser()
    config.read("credentials.conf")
    phone = config.get("CREDENTIALS", "Phone")
    pwd = config.get("CREDENTIALS", "Password")
    print("Config")
    print(phone, pwd)

    # Log in and start processing messages from Whats@pp
    stack.setCredentials((phone, pwd))
    stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
    stack.broadcastEvent(YowLayerEvent(ZmqBrokerLayer.EVENT_START))
    try:
        stack.loop()
    except AuthError as e:
        print("Authentication Error: %s" % e.message)
    except KeyboardInterrupt:
        print("Shutting down.")
        stack.broadcastEvent(YowLayerEvent(ZmqBrokerLayer.EVENT_STOP))
        sys.exit(0)
