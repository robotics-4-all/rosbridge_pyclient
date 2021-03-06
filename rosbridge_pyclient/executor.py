# -*- coding: utf-8 -*-

"""This module provides Threaded and Tornado-compatible backends
fo the executor class.
"""

from __future__ import print_function
import threading
import time
import json
import uuid
from ws4py.manager import WebSocketManager
from pydispatch import dispatcher
import os
import binascii
import hashlib
from ws4py import format_addresses, configure_logger
from ws4py.client import WebSocketBaseClient
from ws4py.client.threadedclient import WebSocketClient as ThreadedWebSocketClient
try:
    from ws4py.client.tornadoclient import TornadoWebSocketClient
    from tornado.ioloop import IOLoop
    TORNADO = True
except ImportError:
    print("[WARNING]: Install tornado to use the ExecutorTornado class, with tornado backend support.")
    TORNADO = False


try:
    import wsaccel
    wsaccel.patch_ws4py()
except ImportError as exc:
    print("[WARNING]: wsaccel python module was not found. XOR masking optimizations wont apply!")


logger = configure_logger()


def get_public_ip():
    from urllib2 import urlopen
    my_ip = urlopen('http://ip.42.pl/raw').read()
    return my_ip


class ExecutorBase(object):
    """Rosbridge websocket protocol executor mixins.
    Manages connections to the server and all interactions with ROS.

    It keeps a record of all publishers, subscribers, service request
    callbacks and action clients.
    """
    MAX_RECONNECTIONS = 20

    def __init__(self, ip="127.0.0.1", port=9090, onopen=None, onclose=None, onerror=None):
        """Executor class constructor.

        Warning: there is a know issue regarding resolving localhost
        to IPv6 address.

        Args:
            ip (str, optional): Rosbridge instance IPv4/Host address.
            Defaults to 'localhost'.
            port (int, optional): Rosbridge instance listening port number.
            Defaults to 9090.
        """
        self._remote_ip = ip
        self._remote_port = port
        self._uri = "ws://{0}:{1}".format(ip, port)
        self._connected = False
        self._id_counter = 0
        self._publishers = {}
        self._publishers_count = {}
        self._subscribers = {}
        self._service_clients = {}
        self._service_servers = {}
        self._action_clients = {}
        self._reconnections = 0
        self._auth_secret = None
        self._bind_callbacks(onopen, onclose, onerror)

    def _bind_callbacks(self, onopen=None, onclose=None, onerror=None):
        setattr(self, "_onopen", onopen)
        setattr(self, "_onclose", onclose)
        setattr(self, "_onerror", onerror)

    @property
    def remote_uri(self):
        return self._uri

    @property
    def connected(self):
        return self.connected

    def gen_id(self):
        """Generate a new ID.

        Current implementation uses an auto-incremental method.

        Returns:
            Incremental ID:
        """
        self._id_counter += 1
        return self._id_counter

    def gen_uuid(self):
        """Generate a new UUID."""
        return str(uuid.uuid4())

    def opened(self):
        """Called when ROSBridge connection over websocket is established.

        Implements the websocket onopened event handler operation.
        """
        self._connected = True
        logger.info('Connected to ROSBridge: {0}'.format(self._uri))
        if callable(self._onopen):
            self._onopen()

    def closed(self, code, reason=None):
        """Called when ROSBridge websocket connection is closed.

        Implements the websocket onclosed event handler operation.

        Args:
            code (int): A status code.
            reason (str, opitonal): A human readable message. Defaults to None.
        """
        self._connected = False
        logger.info('Disconnected from ROSBridge: {}'.format(self._uri))
        logger.info("Reason: {0}, Code: {1}".format(reason, code))
        logger.info("Closed down {0} - {1}\nTiming out for a bit...".format(
            code, reason))
        # self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        self.close()
        if code == 1005:  # Authentication Error
            if self._onautherror is not None:
                self._onautherror()
        #  self._reconnections += 1
        #  if self._reconnections == self.MAX_RECONNECTIONS:
            #  return

    def start(self, onopen=None, onclose=None, onerror=None):
        self._bind_callbacks(onopen, onclose, onerror)
        try:
            self.connect()
            self._connected = True
        except KeyboardInterrupt:
            logger.info("SIGINT Caught. Exiting...")
            self.close()
        except Exception as exc:
            logger.info("Connection refused - {}".format(exc))

    def received_message(self, msg):
        """Called when message is received from ROSBridge websocket server..
        Only handle the message with `topic` or `service`
        keywords and trigger corresponding callback functions.

        Args:
            msg (ws4py.messaging.Message): A message that sent from ROS server.
        """
        data = json.loads(msg.data)
        # Handle subscriber event
        if 'topic' in data:
            dispatcher.send(data.get('topic'), msg=data.get('msg'))
        # handle service response
        if 'service' in data:
            if data.get('op') == 'service_response':
                service_id = data.get('id')
                success = data.get('result')
                values = data.get('values')
                if service_id in self._service_clients:
                    self._service_clients[service_id].callback(success, values)
                    del self._service_clients[service_id]
            elif data.get('op') == 'call_service':
                service_name = data.get('service')
                service_id = data.get('id')
                args = data.get('args')
                if service_name in self._service_servers:
                    result, values = \
                        self._service_servers[service_name].run_handler(args)
                    self.send(json.dumps({
                        'op': 'service_response',
                        'service': service_name,
                        'id': service_id,
                        'result': result,
                        'values': values
                    }))

    def _data_provider(self, data):
        for i in data:
            yield i

    def unhandled_error(self, error):
        """Called when a socket or OS error is raised.

        Args:
            error (str): Human readable error message.
        """
        logger.error("Unhandled error occured: {}".format(error))

    def __del__(self):
        """Destructor. Safely release resources."""
        for publisher in self._publishers:
            if isinstance(self._publishers[publisher], list):
                for p in self._publishers[publisher]:
                    p[publisher].unregister()
            else:
                self._publishers[publisher].unregister()
        for subscriber in self._subscribers:
            if isinstance(self._subscribers[subscriber], list):
                for s in self._subscribers[subscriber]:
                    s[subscriber].unregister()
            else:
                self._subscribers[subscriber].unregister()
        for service_server in self._service_servers:
            self._service_servers[service_server].unregister()
        for action_client in self._action_clients:
            self._action_clients[action_client].unregister()
        if self._connected:
            self.close()

    def register_publisher(self, publisher):
        """Registers a new publisher in the context of the current executor.

        Args:
            publisher (Publisher): The Publisher object.
        """
        topic = publisher.topic
        self.send(json.dumps({
            'op': 'advertise',
            'id': publisher.advertise_id,
            'topic': publisher.topic,
            'type': publisher.message_type,
            'latch': publisher.latch,
            'queue_size': publisher.queue_size
        }))
        if topic in self._publishers:
            self._publishers.get(topic).append(publisher)
        else:
            logger.info('Advertising topic {} for publishing'.format(topic))
            self._publishers[topic] = [publisher]

    def unregister_publisher(self, publisher):
        """Stop advertising on the given topic.

        Args:
            publisher (Publisher): The Publisher object.
        """
        topic = publisher.topic
        self.send(json.dumps({
            'op': 'unadvertise',
            'id': publisher.advertise_id,
            'topic': publisher.topic
        }))
        if topic not in self._publishers:
            return
        publishers = self._publishers.get(topic)
        if publisher in publishers:
            publishers.remove(publisher)
        if len(publishers) == 0:
            del publishers[:]
            del self._publishers[topic]

    def register_subscriber(self, subscriber):
        """Registers a new subscriber in the context of the current executor

        Args:
            subscriber (Subscriber): The subscriber object.
        """
        topic = subscriber.topic
        message_type = subscriber.message_type
        if topic in self._subscribers:
            self._subscribers.get(topic).get('subscribers').append(subscriber)
        else:
            subscribe_id = 'subscribe:{}:{}'.format(topic, self.gen_id())
            logger.info('Sending request to subscribe to topic {}'.format(
                topic))
            msg = json.dumps({
                'op': 'subscribe',
                'id': subscribe_id,
                'topic': topic,
                'type': message_type
            })
            self.send(msg)
            subscriber.subscribe_id = subscribe_id
            dispatcher.connect(subscriber.callback, signal=topic)
            self._subscribers[topic] = {}
            self._subscribers[topic]['subscribe_id'] = subscribe_id
            self._subscribers[topic]['subscribers'] = [subscriber]

    def unregister_subscriber(self, subscriber):
        """Remove a callback subscriber from its topic subscription list.

        If there is no callback subscribers in the subscription list.
        It will unsubscribe the topic.

        Args:
            subscriber (Subscriber): A subscriber with callback function
            that listen to the topic.
        """
        topic = subscriber.topic
        if topic not in self._subscribers:
            return
        #  subscribe_id = self._subscribers.get(topic).get('subscribe_id')
        subscribers = self._subscribers.get(topic).get('subscribers')
        if subscriber in subscribers:
            dispatcher.disconnect(subscriber.callback, signal=topic)
            subscribers.remove(subscriber)
        if len(subscribers) == 0:
            logger.info('Sending request to unsubscribe topic {}'.format(
                topic))
            del subscribers[:]
            self.send(json.dumps({
                'op': 'unsubscribe',
                'id': subscriber.subscribe_id,
                'topic': topic
            }))
            del self._subscribers[topic]

    def register_service_client(self, svcClient, request):
        """Registers a new ServiceClient object.
        It's callback function is called as soon as service responds.

        Args:
            svcClient (ServiceClient): The ServiceClient object to register.
            request (dict): The request arguments.
        """
        _id = svcClient.service_id
        _name = svcClient.name
        if _id in self._service_clients:
            logger.info("Service client with id={0} already registered!")
            return
        self._service_clients[_id] = svcClient
        self.send(json.dumps({
            'op': 'call_service',
            'id': _id,
            'service': _name,
            'args': request
        }))

    def register_action_client(self, action_client):
        action_client.id = self.gen_uuid()
        _id = '{}:{}'.format(action_client.server_name,
                             action_client.action_type)

        if _id in self._action_clients:
            logger.info("Action client with id={0} already registered!")
        else:
            logger.info("Registered Action Client: {}".format(_id))
            self._action_clients[_id] = action_client

    def unregister_action_client(self, action_client):
        _id = '{}:{}'.format(action_client.server_name,
                             action_client.action_type)
        if _id in self._action_clients:
            del self._action_clients[_id]

    def authenticate(self, secret=None, secret_from_file=None, onerror=None):
        setattr(self, "_onautherror", onerror)
        if secret_from_file is not None:
            if os.path.isfile(secret_from_file):
                with open(secret_from_file) as f:
                    self._auth_secret = f.readline().strip("\n")
        elif secret is not None:
            self._auth_secret = secret
        if self._auth_secret is None:
            return False
        rand_hex = binascii.b2a_hex(os.urandom(15))
        user_lvl = "admin"
        dest_ip = self._remote_ip
        source_ip = get_public_ip()
        time_start = 0
        time_stop = 0
        _str = self._auth_secret + source_ip + dest_ip + rand_hex +\
            str(time_start) + user_lvl + str(time_stop)
        _hash = hashlib.sha512(b'{}'.format(_str)).hexdigest()
        auth_msg = {
            "op": "auth",
            "mac": _hash,
            "client": source_ip,
            "dest": dest_ip,
            "rand": rand_hex,
            "t": 0,
            "level": user_lvl,
            "end": 0
        }
        self.send(json.dumps(auth_msg))
        return True


class Executor(ExecutorBase, WebSocketBaseClient):
    """TODO"""
    def __init__(self, *args, **kwargs):
        """Constructor.

        Warning: there is a know issue regarding resolving localhost to
        IPv6 address.

        Args:
            ip (str, optional): Rosbridge instance IPv4/Host address.
            Defaults to 'localhost'.
            port (int, optional): Rosbridge instance listening port number.
            Defaults to 9090.
        """
        ExecutorBase.__init__(self, *args, **kwargs)
        WebSocketBaseClient.__init__(self, self._uri)


class ExecutorThreaded(ExecutorBase, ThreadedWebSocketClient):
    """Threaded implementation of the Executor class"""
    def __init__(self, *args, **kwargs):
        """Constructor.

        Warning: there is a know issue regarding resolving localhost to
        IPv6 address.

        Args:
            ip (str, optional): Rosbridge instance IPv4/Host address.
            Defaults to 'localhost'.
            port (int, optional): Rosbridge instance listening port number.
            Defaults to 9090.
        """
        ExecutorBase.__init__(self, *args, **kwargs)
        ThreadedWebSocketClient.__init__(self, self._uri)

    def start(self):
        """Start executor. Establishes connection to the
        ROSBridge websocket server.
        """
        self.connect()
        self._thread = threading.Thread(target=self.run_forever, name=self.__class__.__name__)
        self._thread.daemon = True
        self._thread.start()
        while not self._connected:
            time.sleep(0.1)

    def start_sync(self):
        self.connect()
        self.run_forever()


if TORNADO:
    class ExecutorTornado(ExecutorBase, TornadoWebSocketClient):
        """Tornado backend implementation of the Executor class."""
        def __init__(self, *args, **kwargs):
            """Constructor.

            Warning: there is a known issue regarding resolving localhost to
            IPv6 address.

            Args:
                ip (str, optional): Rosbridge instance IPv4/Host address.
                Defaults to 'localhost'.
                port (int, optional): Rosbridge instance listening port number.
                Defaults to 9090.
            """
            ioloop = kwargs.get("ioloop", None)
            ExecutorBase.__init__(self, *args, **kwargs)
            TornadoWebSocketClient.__init__(self, self._uri)
            if ioloop is None:
                self._ioLoop = IOLoop.current()
            else:
                self._ioLoop = ioloop

        @property
        def IOLoop(self):
            """Reference to the IOLoop instance. Getter/Setter property."""
            return self._ioLoop

        @IOLoop.setter
        def IOLoop(self, ioloop):
            self._ioLoop = ioloop

        def start(self):
            """Start executor. Establishes connection to the ROSBridge
            websocket server
            """
            self.connect()
            if self._ioLoop._running:
                return
            logger.info("Starting current IOLoop.")
            self._ioLoop.start()

        def stop(self):
            """Stop executor and terminate the IOLoop instance."""
            self.close()
            logger.info("Terminating current IOLoop")
            self._ioLoop.stop()


class ExecutorManager(WebSocketManager):
    """Wraps up ws4py WebSocketManager class, mainly to provide a
    simple graceful stop operation. And because software development is an
    art of mind!
    """
    def __init__(self, *args, **kwargs):
        """ExecutorManager Constructor."""
        WebSocketManager.__init__(self, poller=None, *args, **kwargs)

    def kill(self):
        """Gracefully stop all workers"""
        self.close_all()
        self.stop()
        try:
            self.join()
        except:
            pass
