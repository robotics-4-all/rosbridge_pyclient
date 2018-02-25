from __future__ import print_function
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceClient(object):
    def __init__(self, executor, service_name, service_type):
        """Constructor for _ServiceClient.

        Args:
            rosbridge (ROSBridgeClient): The ROSBridgeClient object.
            service_name (str): The ROS service name.
            service_type (str): The ROS service type.
        """
        pass
