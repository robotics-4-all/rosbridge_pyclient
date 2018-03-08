#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import unittest
import time
from rosbridge_pyclient import Executor, ExecutorManager, ServiceClient

class ServiceClientTest(unittest.TestCase):
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

    def _clb(self, status, data):
        print("Received Message: {0}".format(data))
        self._count += 1
        print(self._count)
        #  if self._count > 2:
            #  self._resF = True
            #  self._managed.close_all()
            #  self._manager.stop()
            #  self._manager.join()


    def test_add_two_ints(self):
        self._svc = ServiceClient(self._exec, "/add_two_ints", "demo_service/AddTwoInts")
        self._svc2 = ServiceClient(self._exec, "/add_two_ints", "demo_service/AddTwoInts")
        resF = False
        req = {
            "a": 1,
            "b": 2
        }
        self._svc.call(req, self._clb)
        self._svc2.call(req, self._clb)
        while self._count < 2:
            time.sleep(0.1)
        self._manager.close_all()
        self._manager.stop()
        self._manager.join()


if __name__ == '__main__':
    unittest.main(verbosity=2)
