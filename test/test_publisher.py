#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import unittest
import time
from rosbridge_pyclient import Executor, ExecutorManager, Publisher, Subscriber

class PubSubTest(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()
        self._manager = ExecutorManager()
        self._manager.start()
        self._exec = Executor()
        self._exec.connect()
        self._manager.add(self._exec)

    def tearDown(self):
        t = time.time() - self.startTime
        print("%s: %.3f" % (self.id(), t))

    def test_publish_string(self):
        self._pub = Publisher(self._exec, "/robot/test_string", "std_msgs/String")
        self._sub = Subscriber(self._exec, "/robot/test_string", "std_msgs/String")
        start = time.time()
        stop = start
        while (stop - start) < 5:
            print(stop - start)
            self._pub.publish({"data": "Publisher {0}".format(self._pub.id)})
            time.sleep(1)
            stop = time.time()
        self._pub.unregister()
        self._manager.stop()


if __name__ == '__main__':
    unittest.main(verbosity=2)
