#!/usr/bin/env python3
from zmqlayer import ZmqBrokerLayer

from yowsup.layers.axolotl                     import YowAxolotlLayer
from yowsup.layers.auth                        import YowCryptLayer, YowAuthenticationProtocolLayer, AuthError
from yowsup.layers.coder                       import YowCoderLayer
from yowsup.layers.network                     import YowNetworkLayer
from yowsup.layers.protocol_messages           import YowMessagesProtocolLayer
from yowsup.layers.protocol_media              import YowMediaProtocolLayer
from yowsup.layers.stanzaregulator             import YowStanzaRegulator
from yowsup.layers.protocol_receipts           import YowReceiptProtocolLayer
from yowsup.layers.protocol_acks               import YowAckProtocolLayer
from yowsup.layers.logger                      import YowLoggerLayer
from yowsup.layers.protocol_iq                 import YowIqProtocolLayer
from yowsup.layers.protocol_calls              import YowCallsProtocolLayer
from yowsup.layers import YowLayerEvent, YowParallelLayer
from yowsup.stacks import YowStack, YowStackBuilder

import sys
import configparser


if __name__==  "__main__":
    # layers = (
    #     EchoLayer,
    #     YowParallelLayer((YowAuthenticationProtocolLayer, YowMessagesProtocolLayer, YowReceiptProtocolLayer, YowAckProtocolLayer, YowMediaProtocolLayer, YowIqProtocolLayer, YowCallsProtocolLayer)),
    #     YowAxolotlLayer,
    #     YowLoggerLayer,
    #     YowCoderLayer,
    #     YowCryptLayer,
    #     YowStanzaRegulator,
    #     YowNetworkLayer
    # )
    # stack = YowStack(layers)
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

    # Log in and start processing messages from Whatsapp
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
