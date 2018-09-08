#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import unittest
import time
from rosbridge_pyclient import Executor, ExecutorManager, ActionClient, Goal
from pprint import pprint

class ActionClientTest(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()
        self._manager = ExecutorManager()
        self._manager.start()
        self._exec = Executor(ip="83.212.96.15", port="8115")
        self._exec.connect()
        self._manager.add(self._exec)
        self._exec.authenticate("44UCmQiX3mZtxC7y", onerror=self._onautherror)
        self._goal_reached = False

    def tearDown(self):
        t = time.time() - self.startTime
        print("%s: %.3f" % (self.id(), t))
        self._manager.kill()

    def _onautherror(self):
        print("AUTHENTICATION ERROR!")

    def _on_result(self, data, status, header):
        print("Received Result: ")
        pprint(data)
        pprint(status)
        pprint(header)
        self._goal_reached = True

    def _on_feedback(self, data, status, header):
        print("Received Feedback: ")
        pprint(data)
        pprint(status)
        pprint(header)

    def _on_status(self, data, header):
        print("Received Status: ")
        pprint(data)
        pprint(header)

    def test_move_base(self):
        server_name = "robot1/move_base"
        action_type = "move_base_msgs/MoveBase"
        req = {
            "target_pose": {
                "frame_id": "world",
                "pose": {
                    "position": {
                        "x": 0.0
                    },
                    "orientation": {
                        "w": 1.0
                    }
                }
            }
        }
        self.ac = ActionClient(self._exec, server_name, action_type)
        self.goal = Goal(req, on_result=self._on_result,
                         on_feedback=self._on_feedback,
                         on_status=self._on_status)
        self.ac.send_goal(self.goal)

        while not self._goal_reached:
            time.sleep(0.2)
        self._manager.close_all()
        self._manager.stop()
        self._manager.join()


if __name__ == '__main__':
    unittest.main(verbosity=2)
