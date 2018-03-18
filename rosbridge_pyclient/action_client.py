#!/usr/bin/env python

from __future__ import print_function, absolute_import

from .subscriber import Subscriber
from .publisher import Publisher

import uuid
import logging

try:
    basestring
except NameError:
    # Python3 compatibility
    basestring = str

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActionClient(object):
    def __init__(self, executor, server_name, action_type):
        """Constructor.

        Args:
            executor (Underlaying ros command executor instance):
            The [Executor|ExecutorThreadedu|ExecutorTornado] object.
            server_name (str): The ROS action server name.
            action_type (str): The ROS action name.
        """
        self._executor = executor
        self._server_name = server_name
        self._action_type = action_type
        self._goals = {}
        self._id = ""

        self._feedback_sub = Subscriber(self._executor,
                                        '{0}/feedback'.format(server_name),
                                        '{0}ActionFeedback'.format(action_type),
                                        self.on_feedback)
        self._result_sub = Subscriber(self._executor,
                                        '{0}/result'.format(server_name),
                                        '{0}ActionResult'.format(action_type),
                                        self.on_result)
        self._status_sub = Subscriber(self._executor,
                                        '{0}/status'.format(server_name),
                                        'actionlib_msgs/GoalStatusArray',
                                        self.on_statusChanged)
        self._goal_pub = Publisher(self._executor,
                                   '{0}/goal'.format(server_name),
                                   '{0}ActionGoal'.format(action_type))
        self._cancel_pub = Publisher(self._executor,
                                     '{0}/cancel'.format(server_name),
                                     'actionlib_msgs/GoalID')

    @property
    def server_name(self):
        return self._server_name

    @property
    def action_type(self):
        return self._action_type

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, val):
        self._id = val

    def on_statusChanged(self, message):
        goal = self._goals.get(message.get('status_list')[0].get('goal_id').get('id'))
        if goal:
            goal.status_received(message.get('status_list'))

    def on_feedback(self, msg):
        """Callback when a feedback message received.
        Args:
            message (dict): A feedback message received feedbackrom ROS action server.
        """
        logger.info("Feedback: {}".format(msg))
        goal = self._goals.get(msg.get('status').get('goal_id').get('id'))
        if goal:
            goal.feedback_received(msg.get(
                'feedback'), msg.get('status'))

    def on_result(self, msg):
        """Callback when a result message received.
        Args:
            message (dict): A result message received from ROS action server.
        """
        goal = self._goals.get(msg.get('status').get('goal_id').get('id'))
        if goal:
            goal.result_received(msg.get('result'), msg.get('status'))

    def send_goal(self, goal):
        """Send a goal to the ROS action server.
        Args:
            goal_message (dict): A message to send to ROS action server.
            on_result (function): A callback function to be called when a
                feedback message received.
            on_feedback (function): A callback function to be called when a
                result message received.
        """
        self._goals[goal.id] = goal
        self._goal_pub.publish(goal.message)
        return goal.id

    def cancel_goal(self, goal_id):
        """Cancel a goal with a given goal ID
        Args:
            goal_id (str): The ID of the goal to be cancelled.
        """
        self._cancel_pub.publish({'id': goal_id})

    def unregister(self):
        """Reduce the usage of the action client. If the usage is 0,
        unregister its publishers and subscribers."""
        self._usage -= 1
        if self._usage == 0:
            self._feedback_sub.unregister()
            self._result_sub.unregister()
            self._goal_pub.unregister()
            self._cancel_pub.unregister()
            self._rosbridge.unregister_action_client(self)

    def _register(self):
        self._executor.register_action_client(self)


class Goal(object):
    def __init__(self, message, on_result=None, on_feedback=None, on_status=None):
        """Constructor for _Goal
        Args:
            message (dict): The goal message to send to ROS action server.
            on_result (function): A callback function to be called when a
                feedback message received.
            on_feedback (function): A callback function to be called when a
                result message received.
        """
        self._id = 'goal_' + str(uuid.uuid4())
        self._message = message
        self._is_finished = False
        self._on_result = on_result
        self._on_feedback = on_feedback
        self._on_status = on_status

    @property
    def id(self):
        return self._id

    @property
    def message(self):
        """Wrap message in JSON format that complies ROSBridge protocol.
        Returns:
            A JSON that contains the goal ID and message.
        """
        return {
            'goal_id': {
                'stamp': {
                    'secs': 0,
                    'nsecs': 0
                },
                'id': self._id
            },
            'goal': self._message
        }

    @message.setter
    def message(self, val):
        self._message = val

    @property
    def is_finished(self):
        return self._is_finished

    def _on_result_wrap(self, msg, status):
        self._on_result(msg, status)

    def _on_feedback_wrap(self, msg, status):
        self._on_feedback(msg, status)

    def result_received(self, result, status):
        """Called when a result message is received from the Action Server (AS).
        Args:
            result (dict): The result message.
            status (int): The status code. Such as:
                ACTIVE = 1: The goal is currently being processed by the AS;
                PREEMPTED = 2: The goal received a cancel request after it
                    started executing;
                SUCCEEDED = 3: The goal was achieved successfully by the AS;
                ABORTED = 4: The goal was aborted during execution by the AS
                    due to some failure.
                For more details, refer to
                http://docs.ros.org/indigo/api/actionlib_msgs/html/msg/GoalStatus.html.
        """
        self._is_finished = True
        self._message = result
        if callable(self._on_result):
            self._on_result_wrap(result, status)

    def feedback_received(self, feedback, status):
        """Called when a result message is received.
        Args:
            feedback (dict): The feedback message.
            status (int): The status code. Such as:
                ACTIVE = 1: The goal is currently being processed by the AS;
                PREEMPTED = 2: The goal received a cancel request after it
                    started executing;
                SUCCEEDED = 3: The goal was achieved successfully by the AS;
                ABORTED = 4: The goal was aborted during execution by the AS
                    due to some failure.
                For more details, refer to
                http://docs.ros.org/indigo/api/actionlib_msgs/html/msg/GoalStatus.html.
        """
        if callable(self._on_feedback):
            self._on_feedback_wrap(feedback, status)

    def status_received(self, status):
        """Called when a result message is received.
        Args:
            feedback (dict): The feedback message.
            status (int): The status code. Such as:
                ACTIVE = 1: The goal is currently being processed by the AS;
                PREEMPTED = 2: The goal received a cancel request after it
                    started executing;
                SUCCEEDED = 3: The goal was achieved successfully by the AS;
                ABORTED = 4: The goal was aborted during execution by the AS
                    due to some failure.
                For more details, refer to
                http://docs.ros.org/indigo/api/actionlib_msgs/html/msg/GoalStatus.html.
        """
        if callable(self._on_status):
            self._on_status(status)
