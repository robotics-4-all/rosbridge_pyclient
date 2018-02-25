# -*- coding: utf-8 -*-

from __future__ import print_function
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Publisher(object):
    def __init__(self, executor, topic_name, message_type, latch=False, queue_size=1):
        """Constructor.

        Args:
            executor (ExecutorThreaded/ExecutorTornado): An executor object.
            topic_name (str): The ROS topic name.
            message_type (str): The ROS message type, such as `std_msgs/String`.
            latch (bool, optional): Whether the topic is latched when publishing. Defaults to False.
            queue_size (int): The queue created at bridge side for re-publishing. Defaults to 1.
        """
        self._id = executor.gen_id()
        self._advertise_id = 'advertise:{}:{}'.format(topic_name, self._id)
        self._executor = executor
        self._topic_name = topic_name
        self._message_type = message_type
        self._latch = latch
        self._queue_size = queue_size
        self._register()

    @property
    def id(self):
        return self._id

    @property
    def advertise_id(self):
        return self._advertise_id

    @property
    def queue_size(self):
        return self._queue_size

    @property
    def message_type(self):
        return self._message_type

    @property
    def latch(self):
        """Publishing latch status. Boolean"""
        return self._latch

    @property
    def queue_size(self):
        """Publishing topic queue size"""
        return self._queue_size

    @property
    def topic(self):
        """Getter only property. Returns publishing topic name."""
        return self._topic_name

    def publish(self, message):
        """Publish a ROS message

        Args:
            message (dict): A message to send.
        """
        logger.info("Publishing to topic [{0}]: {1}".format(self._topic_name, message))
        self._executor.send(json.dumps({
            'op': 'publish',
            'id': 'publish:{0}:{1}'.format(self._topic_name, self._id),
            'topic': self._topic_name,
            'msg': message
        }))

    def unregister(self):
        """Reduce the usage of the publisher. If the usage is 0, unadvertise this topic."""
        self._executor.unregister_publisher(self)

    def _register(self):
        self._executor.register_publisher(self)

    def start(self):
        self._register()

    def __del___(self):
        """Destructor"""
        self.unregister()

