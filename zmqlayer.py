#!/usr/bin/env python3

import hashlib
from concurrent.futures import Future

from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_groups.protocolentities import CreateGroupsIqProtocolEntity, \
    CreateGroupsNotificationProtocolEntity
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity

from zmqserver import ZmqInterface


def zmqrpc(func):
    """Decorator that enables remote access to the decorated function.
    """
    if not hasattr(func, "__call__"):
        raise ValueError("%s not callable." % func)

    func.__remote_yowsup__ = True
    return func


class ZmqBrokerLayer(ZmqInterface, YowInterfaceLayer):
    EVENT_START = "yowsup.zmqlayer.event.start"
    EVENT_STOP = "yowsup.zmqlayer.event.stop"

    def __init__(self):
        super(ZmqBrokerLayer, self).__init__()
        YowInterfaceLayer.__init__(self)
        self.connected = False

        self.group_association = {}

    @staticmethod
    def normalize_jid(number):
        if '@' in number:
            return number

        return str(number) + "@s.whatsapp.net"

    @staticmethod
    def calc_numbers_hash(jids):
        # Arrange numbers to create deterministic pattern
        phone_numbers = [x.split('@', 1)[0] for x in jids]
        phone_numbers.sort()

        # Align all numbers as string
        buffer = bytearray()
        for jid in phone_numbers:
            buffer.extend(jid.encode())

        # Hash for unique length
        return hashlib.sha1(buffer).hexdigest()

    def onEvent(self, layerEvent):
        if layerEvent.getName() == self.__class__.EVENT_START:
            print("Received start event.")
            # Start ZMQ request server
            self.start_server()
            return True

        elif layerEvent.getName() == self.__class__.EVENT_STOP:
            print("Received stop event.")
            # Stop ZMQ request server
            self.stop_server()
            return True

        # Do not consume any other events (e.g. connecting yowsup)
        return False

    ##################################################################
    # Incoming telegrams
    ##################################################################
    @ProtocolEntityCallback("success")
    def onSuccess(self, entity):
        self.connected = True
        print("Login successful.")
        # self.call_it()

    @ProtocolEntityCallback("failure")
    def onLoginFailure(self, entity):
        self.connected = False
        print("Could not login on Whats@pp. Reason: " + entity.getReason())


    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        out = "Msg: "

        if messageProtocolEntity.getType() == "text":
            # self.output(message.getBody(), tag = "%s [%s]"%(message.getFrom(), formattedDate))
            out += messageProtocolEntity.getBody()
        elif messageProtocolEntity.getType() == "media":
            out += "[Media Type:"
            if messageProtocolEntity.getMediaType() in ("image", "audio", "video"):
                out += "{media_type}, Size:{media_size}, URL:{media_url}]".format(
                    media_type = messageProtocolEntity.getMediaType(),
                    media_size = messageProtocolEntity.getMediaSize(),
                    media_url = messageProtocolEntity.getMediaUrl()
                )
        print(out)

        self.toLower(messageProtocolEntity.ack())
        self.toLower(messageProtocolEntity.ack(True))

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        self.toLower(entity.ack())

    @ProtocolEntityCallback("chatstate")
    def onChatstate(self, entity):
        print("Chatstate: {}".format(entity))

    @ProtocolEntityCallback("iq")
    def onIq(self, entity):
        print("iq: {}".format(entity.__str__()))

    @ProtocolEntityCallback("notification")
    def onNotification(self, notification):
        # Handle CreateGroupsNotification
        if isinstance(notification, CreateGroupsNotificationProtocolEntity):
            # Find corresponding group creation future and notify ZMQ broker
            jids = notification.getParticipants().keys()
            group_hash = self.calc_numbers_hash(jids)

            fut = self.group_association.pop(group_hash)
            if fut:
                fut.set_result(notification)

        print(type(notification))
        print("Notification: From :{}, Type: {}".format(notification.getFrom(), notification.getType()))

        self.toLower(notification.ack())

    ##################################################################
    # Outgoing telegrams
    ##################################################################
    @zmqrpc
    def message_send(self, number, msg):
        """
        Transmit a text message to a recipient.
        :param number:
            mobile number (without + or 00) or Jid of the recipient
        :type number: str
        :param msg:
            message text to transmit.
        :type msg: str|bytes

        :return:
        """
        if isinstance(msg, str):
            msg = msg.encode("utf-8")

        outgoingMessage = TextMessageProtocolEntity(msg, to=self.normalize_jid(number))
        self.toLower(outgoingMessage)

        # Assume successful transmission
        fut = Future()
        fut.set_result("Done")

        return fut

    @zmqrpc
    def group_create(self, subject, numbers):
        jids = [self.normalize_jid(jid) for jid in numbers.split(',')] if numbers else []

        if len(jids) >= 2:
            print("Group: subject: {0}, jids: {1}".format(subject, jids))
            # Calculate unique group identifier to re-identify Whats@pp notification
            # on creating this group
            group_hash = self.calc_numbers_hash(jids)

            # Notify our ZMQ broker as soon as the right notification with GID comes in
            fut = Future()
            self.group_association[group_hash] = fut

            # Create Whats@pp group
            entity = CreateGroupsIqProtocolEntity(subject, participants=jids)
            self.toLower(entity)

            return fut

        return None
