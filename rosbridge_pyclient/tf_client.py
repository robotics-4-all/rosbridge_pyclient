#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function, absolute_import

class TFClient(object):
    def __init__(self, executor, frame_id, clb):
        """Constructor.

        Kwargs:
            executor (ExecutorThreaded/ExecutorTornado): An executor object.
            frame_id (str): The base tf frame id.
            clb (function): A function will be called when a message is received on that topic.
        """
        self._frame_id_base = frame_id
        # Registration of callback function is handled by the Subscriber
        Subscriber.__init__(self, executor, clb)
