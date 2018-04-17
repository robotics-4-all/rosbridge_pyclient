#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import time
from rosbridge_pyclient import Executor, ExecutorManager
import os

DIRPATH = os.path.dirname(os.path.realpath(__file__))

manager = ExecutorManager()


def onautherror():
    print("AUTHENTICATION ERROR!")
    manager.kill()


if __name__ == '__main__':
    manager.start()
    executor = Executor(ip="83.212.96.15", port=8127)
    executor.connect()
    manager.add(executor)
    executor.authenticate("DDccaldGJdYNSuod", onerror=onautherror)
