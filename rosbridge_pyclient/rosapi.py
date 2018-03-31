#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import

import time
from functools import wraps

from .service_client import ServiceClient
from .executor import Executor, ExecutorManager

try:
    basestring
except NameError:
    basestring = str


class AuthenticationMixin(object):
    def authenticate(self, secret=None):
        self._executor.authenticate(secret)


class ParameterServerMixins(object):
    def has_param(self, param, clb=None):
        """Returns true if given ROS Parameter exists, false otherwise.
        
        Args:
            param (str): The ROS Parameter name.
            clb (function, optional): Callback function that is called upon response is received.
        """
        req = {
            "name": param
        }
        status, data = self._call(clb, req, "/rosapi/has_param", "rosapi/HasParam")
        data = data.get("exists", None) if not isinstance(data, basestring) else data
        return status, data

    def get_param(self, param, default="", clb=None):
        """Returns the value of given ROS Parameter.
        
        Args:
            param (str): The ROS Parameter name.
            default (str, optional): Default value.
            clb (function, optional): Callback function that is called upon response is received.
        """
        req = {
            "name": param,
            "default": default
        }
        status, data = self._call(clb, req, "/rosapi/get_param", "rosapi/GetParam")
        data = data.get("value", None) if not isinstance(data, basestring) else data
        return status, data

    def set_param(self, param, value, clb=None):
        """Sets the value of given ROS Parameter.
        
        Args:
            param (str): The ROS Parameter name.
            value (str, optional): Parameter value.
            clb (function, optional): Callback function that is called upon response is received.
        """
        req = {
            "name": param,
            "value": value
        }
        status, data = self._call(clb, req, "/rosapi/set_param", "rosapi/SetParam")
        return status, data

    def get_params_names(self, clb=None):
        """
        req = {}
        resp = {names: []}
        """
        raise NotImplementedError()

    def delete_param(self, param, clb=None):
        """req = {name: ''}, resp = {}"""
        raise NotImplementedError()


class ServiceOperationMixins(object):
    def get_services(self, clb=None):
        """Returns a list of currently alive ROS Services."""
        req = {}
        status, data = self._call(clb, req, "/rosapi/services", "rosapi/Services")
        data = data.get("services", None) if not isinstance(data, basestring) else data
        return status, data

    def get_service_type(self, svc_name, clb=None):
        """TODO.
        Args:
            svc (str): The ROS Service name.
            clb (function, optional): Callback function that is called upon response is received.
        """
        req = {
            "service": svc_name
        }
        status, data = self._call(clb, req, "/rosapi/service_type", "rosapi/ServiceType")
        data = data.get("type", None) if not isinstance(data, basestring) else data
        return status, data

    def get_services_for_type(self, svc_type, clb=None):
        """Returns a list of services of given type
        
        Args:
            svc_type (str): The ROS Service type.
            clb (function, optional): Callback function that is called upon response is received.
        """
        req = {
            "type": topic_type
        }
        status, data = self._call(clb, req, "/rosapi/services_for_type", "rosapi/ServicesForType")
        data = data.get("services", None) if not isinstance(data, basestring) else data
        return status, data


class TopicOperationsMixins(object):
    def get_topics(self, clb=None):
        """Returns a list of currently alive ROS Topics. Similar to `rostopic list`
        Args:
            topic_type (str): The Topic type.
            clb (function, optional): Callback function that is called upon response is received.
        """
        req = {}
        status, data = self._call(clb, req, "/rosapi/topics", "rosapi/Topics")
        data = data.get("topics", None) if not isinstance(data, basestring) else data
        return status, data

    def get_topic_type(self, topic_name, clb=None):
        """Returns a list of currently alive ROS Topics. Similar `rostopic type <topic_type>`.
        Args:
            topic_name (str): The Topic name.
            clb (function, optional): Callback function that is called upon response is received.
        """
        req = {
            "topic": topic_name
        }
        status, data = self._call(clb, req, "/rosapi/topic_type", "rosapi/TopicType")
        data = data.get("type", None) if not isinstance(data, basestring) else data
        return status, data

    def get_topics_for_type(self, topic_type, clb=None):
        """Returns a list of topics of given type
        
        Args:
            topic_type (str): The Topic type.
            clb (function, optional): Callback function that is called upon response is received.
        """
        req = {
            "type": topic_type
        }
        status, data = self._call(clb, req, "/rosapi/topics_for_type", "rosapi/TopicsForType")
        data = data.get("topics", None) if not isinstance(data, basestring) else data
        return status, data


class PublisherOperationsMixins(object):
    def get_publishers(self, clb=None):
        """Returns a list of currently alive ROS Publishers."""
        req = {}
        status, data = self._call(clb, req, "/rosapi/publishers", "rosapi/Publishers")
        data = data.get("publishers", None) if not isinstance(data, basestring) else data
        return status, data


class SubscriberOperationsMixins(object):
    def get_subscribers(self, clb=None):
        """Returns a list of currently alive ROS Subscribers."""
        req = {}
        status, data = self._call(clb, req, "/rosapi/subscribers", "rosapi/Subscribers")
        data = data.get("subscribers", None) if not isinstance(data, basestring) else data
        return status, data


class NodeOperationsMixins(object):
    def get_nodes(self, clb=None):
        """Returns a list of currently alive ROS Nodes."""
        req = {}
        status, data = self._call(clb, req, "/rosapi/nodes", "rosapi/Nodes")
        data = data.get("nodes", None) if not isinstance(data, basestring) else data
        return status, data

    def get_node_details(self, node_name, clb=None):
        """Return detailes of given node. Include list of subscribers, publishers and services."""
        req = {
            "node": node_name
        }
        status, data = self._call(clb, req, "/rosapi/node_details", "rosapi/NodeDetails")
        return status, data


class ROSApi(ParameterServerMixins, ServiceOperationMixins,
             TopicOperationsMixins, PublisherOperationsMixins,
             SubscriberOperationsMixins, NodeOperationsMixins,
             AuthenticationMixin):
    def __init__(self, executor=None, ip="127.0.0.1", port="9090"):
        if executor is None:
            self._manager = ExecutorManager()
            self._manager.start()
            self._executor = Executor(ip=ip, port=port)
            self._executor.start()
            self._manager.add(self._executor)
        else:
            self._executor = executor

    def _callback(self, status, data):
        self.__data = data
        self.__status = status
        self.__resF = True

    def _call(self, clb, req, svc_name, svc_type):
        svc = ServiceClient(self._executor, svc_name, svc_type)
        if clb is None:
            self._svc = svc
            self.__resF = False
            self.__data = {}
            self.__status = -1
            self._svc.call(req, self._callback)
            while self.__resF is False:
                time.sleep(0.001)
            return self.__status, self.__data
        return svc.call(req, clb)

    def get_action_servers(self, clb=None):
        req = {}
        status, data = self._call(clb, req, "/rosapi/action_servers", "rosapi/GetActionServers")
        # TODO: Does not seem to work with indigo!!!!!
        data = data.get("*", None) if not isinstance(data, basestring) else data
        return status, data

    def stop(self):
        if self._manager is not None:
            self._manager.kill()
