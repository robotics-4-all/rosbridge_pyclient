#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import unittest
import time
from rosbridge_pyclient import ROSApi

SECRET_KEY="NfMhPEH7LmIMr57U"


class ROSApiTest(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()
        self.ros = ROSApi(ip="83.212.96.15", port="8115")
        self.ros.authenticate(secret=SECRET_KEY)

    def tearDown(self):
        t = time.time() - self.startTime
        print("%s: %.3f" % (self.id(), t))
        self.ros.stop()

    def _clb(self, status, data):
        self._print("Received Message: {0}".format(data))
        self._count += 1

    def test_get_nodes(self):
        _, ac = self.ros.get_nodes()
        self._print("Service [{}] returned: {}".format('/rosapi/nodes', ac))

    def test_get_node_details(self):
        node = "/rosout"
        _, ac = self.ros.get_node_details(node)
        self._print("Service [{}] returned: {}".format('/rosapi/node_details', ac))

    def test_get_publishers(self):
        _, ac = self.ros.get_publishers('/clock')
        self._print("Service [{}] returned: {}".format('/rosapi/publishers', ac))

    def test_get_subscribers(self):
        _, ac = self.ros.get_subscribers('/clock')
        self._print("Service [{}] returned: {}".format('/rosapi/subscribers', ac))

    def test_get_topics(self):
        _, ac = self.ros.get_topics()
        self._print("Service [{}] returned: {}".format('/rosapi/topics', ac))

    def test_get_topic_type(self):
        topic_name = "/rosout"
        _, ac = self.ros.get_topic_type(topic_name)
        self._print("Service [{}] returned: {}".format('/rosapi/topic_type', ac))

    def test_get_topics_for_type(self):
        topic_type = "rosgraph_msgs/Log"
        _, ac = self.ros.get_topics_for_type(topic_type)
        self._print("Service [{}] returned: {}".format('/rosapi/topics_for_type', ac))

    def test_get_services(self):
        _, ac = self.ros.get_services()
        self._print("Service [{}] returned: {}".format('/rosapi/services', ac))

    def test_has_param(self):
        param = "/rosversion"
        _, ac = self.ros.has_param(param)
        self._print("Service [{}%param='{}'] returned: {}".format('/rosapi/has_param', param, ac))

    def test_get_param(self):
        param = "/rosversion"
        _, ac = self.ros.get_param(param)
        self._print("Service [{}%param='{}'] returned: {}".format('/rosapi/get_param', param, ac))

    def test_set_param(self):
        param = "/rosversion"
        value = "10"
        _, ac = self.ros.set_param(param, value)
        self._print("Service [{}%param='{}%value={}'] returned: {}".format('/rosapi/set_param', param,
                                                                           value, ac))


    def _print(self, msg):
        print("\033[94m{}\033[0m'".format(msg))

if __name__ == '__main__':
    unittest.main(verbosity=2)
