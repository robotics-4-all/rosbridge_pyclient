from __future__ import print_function
import json
import logging
from pydispatch import dispatcher

try:
    basestring
except NameError:
    basestring = str

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Subscriber(object):
    def __init__(self, executor, topic_name, message_type, clb=None):
        """Constructor.

        Args:
            executor (ExecutorThreaded/ExecutorTornado): An executor object.
            topic_name (str): The ROS topic name.
            clb (function): A function will be called when a message is received on that topic.
        """
        self._executor = executor
        self._topic_name = topic_name
        if clb is not None:
            self._clb = clb
        self._message_type = message_type
        self._id = executor.gen_id()
        self._subscribe_id = ""
        # Store callback function for future use
        self._register()

    @property
    def topic(self):
        """Subsriber Topic name. Getter only property"""
        return self._topic_name

    @property
    def message_type(self):
        """Topic message type. E.g. 'std_msgs/String'"""
        return self._message_type

    @property
    def id(self):
        """Subscriber object unique numerical id. Specified by the executor dynamically"""
        return self._id

    @property
    def subscribe_id(self):
        """Subsribe id, required by the ROSBridge API. Getter only property"""
        return self._subscribe_id

    @subscribe_id.setter
    def subscribe_id(self, value):
        if isinstance(value, basestring):
            self._subscribe_id = value

    @property
    def callback(self):
        """On-Message callback function. Getter only property"""
        return self._clb

    def unregister(self):
        """Remove the current callback function from listening to the topic,
        and from the rosbridge client subscription list
        """
        self._executor.unregister_subscriber(self)

    def _register(self):
        """TODO"""
        self._executor.register_subscriber(self)

    def _clb(self, message):
        logger.info(message)

    def __del__(self):
        """Destructor"""
        self.unregister()
