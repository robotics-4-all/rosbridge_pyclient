#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import unittest
import time
from rosbridge_pyclient import Executor, ExecutorManager
import os

DIRPATH = os.path.dirname(os.path.realpath(__file__))
SECRET_FILE = os.path.join(DIRPATH, "auth.secret")


class AuthenticationTest(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()
        self._manager = ExecutorManager()
        self._manager.start()
        self._exec = Executor(ip="83.212.96.15", port=8115)
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

    def test_auth_pass_secret(self):
        self._exec.authenticate("NfMhPEH7LmIMr57U")
        time.sleep(1)
        self._manager.kill()

    def test_auth_pass_secret_filepath(self):
        self._exec.authenticate(secret_from_file=SECRET_FILE)
        time.sleep(2)
        self._manager.kill()


if __name__ == '__main__':
    unittest.main(verbosity=2)
