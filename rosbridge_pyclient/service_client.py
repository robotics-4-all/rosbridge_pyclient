from __future__ import print_function
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceClient(object):
    def __init__(self, executor, service_name, service_type):
        """Constructor for _ServiceClient.

        Args:
            executor  (Executor/ExecutorThreaded/ExecutorTornado): The ROSBridgeClient object.
            service_name (str): The ROS service name.
            service_type (str): The ROS service type.
        """
        self._executor = executor
        self._service_name = service_name
        self._service_type = service_type
        self._id = self._executor.gen_id()
        self._service_id = 'call_service:{}:{}'.format(self._service_name, self._id)
        self._clb = None

    @property
    def id(self):
        """Service unique numerical id. Getter only property"""
        return self._id

    @property
    def name(self):
        """Service Name property. Getter only"""
        return self._service_name

    @property
    def type(self):
        """Service type property. Getter only"""
        return self._service_type

    def call(self, req_msg, cb):
        """Send a request to the ROS service server. The callback function will be called when service responses.
        Args:
            request (dict): A request message to send,
            cb (function): A function will be called when the service server responses. callback(success, message)
        """
        if callable(cb):
            self._clb = clb
            self._executor.register_service_client(self, req_msg)

    @property
    def callback(self):
        """Registered callback function of this service client
        callback(success, message).
        Getter only property. Returns the callback function pointer.
        """
        return self._clb
