#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import unittest
import time
from rosbridge_pyclient import Executor, ExecutorManager, ActionClient, Goal

class ActionClientTest(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()
        self._manager = ExecutorManager()
        self._manager.start()
        self._exec = Executor()
        self._exec.connect()
        self._manager.add(self._exec)
        self._count = 0

    def tearDown(self):
        t = time.time() - self.startTime
        print("%s: %.3f" % (self.id(), t))

    def _on_result(self, data, status):
        print("Received Result: {0}".format(data))
        self._count += 1

    def _on_feedback(self, data, status):
        print("Received Feedback: {0}".format(data))

    def test_fibonacci(self):
        server_name = "fibonacci"
        action_type = "demo_action_server/Fibonacci"
        self.ac = ActionClient(self._exec, server_name, action_type)
        self.goal = Goal({'order': 7}, on_result=self._on_result, on_feedback=self._on_feedback)
        self.ac.send_goal(self.goal)
        resF = False
        req = {
            "a": 1,
            "b": 2
        }
        while self._count == 0:
            time.sleep(0.2)
        self._manager.close_all()
        self._manager.stop()
        self._manager.join()


if __name__ == '__main__':
    unittest.main(verbosity=2)
