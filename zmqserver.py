import threading
import zmq
import inspect

from yowsup.layers.protocol_groups.protocolentities import CreateGroupsNotificationProtocolEntity


class ZmqInterface(object):
    def __init__(self):
        self.pub_commands = {}
        self.worker_thread = None

        members = inspect.getmembers(self, predicate=inspect.ismethod)
        # print(members)

        for (func_name, func_handler) in members:
            if hasattr(func_handler, '__remote_yowsup__'):
                self.pub_commands[func_name] = {
                    "fn": func_handler,
                    "args": inspect.getargspec(func_handler)[0][1:]
                }
                print(self.pub_commands[func_name])

        self.worker_thread = ZmqServer(self.pub_commands)

    def start_server(self):
        self.worker_thread.start()

    def stop_server(self):
        self.worker_thread.running = False


class ZmqServer(threading.Thread):
    """Server worker thread"""
    def __init__(self, exposed_commands):
        super(ZmqServer, self).__init__()
        self.running = True

        self.context = zmq.Context()
        self.zmqsock = self.context.socket(zmq.REP)
        self.zmqsock.bind("tcp://127.0.0.1:%s" % 5555)
        self.cmds = exposed_commands

    def run(self):
        print("ZMQ worker thread started.")

        while self.running:
            print("waiting for next command...")
            msg = self.zmqsock.recv_json()
            print("Rcv msg: {}".format(msg))

            # Route message to handler function if available
            func_name = msg.get("cmd", "")
            if func_name in self.cmds:
                handler = self.cmds[func_name]

                # Map all params to its matching function parameters
                params = []
                for p in handler["args"]:
                    value = msg.get(p, None)
                    params.append(value)

                # Execute RPC and handle future result
                fut = handler["fn"](*params)
                if fut:
                    try:
                        res = fut.result(5)

                        server_response = {"status": "success"}
                        server_response.update(self.process_notification(res))
                        self.zmqsock.send_json(server_response)

                    except Exception as ex:
                        print("Could not associate creategroup. Exception: {}".format(ex.__str__()))
                        # Generic reply if something went wrong
                        self.zmqsock.send_json({"status": "failure"})

                else:
                    # Missing future not allowed anymore
                    self.zmqsock.send_json({"status": "failure"})

        print("Stopped.")

    @staticmethod
    def process_notification(notification):
        if isinstance(notification, CreateGroupsNotificationProtocolEntity):
            gid = notification.getFrom(full=False)
            timestamp = notification.getCreationTimestamp()
            participants = [x.split('@', 1)[0] for x in notification.getParticipants().keys()]

            return {
                "gid": gid,
                "timestamp_creation": timestamp,
                "participants": participants
            }

        return {}