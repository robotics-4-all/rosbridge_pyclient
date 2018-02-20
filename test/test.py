#!/usr/bin/env python
# coding: utf-8

#  from rosbridge_pyclient import ExecutorThreaded
#  from rosbridge_pyclient import ExecutorTornado
#  from rosbridge_pyclient import ExecutorManager
from rosbridge_pyclient import *
from tornado.ioloop  import IOLoop
import time

if __name__ == "__main__":
    try:
        #  m = ExecutorManager()
        #  m.start()
        e1 = ExecutorThreaded(ip="127.0.0.1")
        e1.connect()
        #  e2 = ExecutorTornado(ip="127.0.0.1")
        #  e2.connect()
        #  m.add(e2)
        s = Subscriber(e1, "/robot/test", "std_msgs/String")
        # p = Publisher(e2, "/robot/test", "std_msgs/String")
        #  IOLoop.current().start()
        p = Publisher(e1, "/robot/test", "std_msgs/String")
        p2 = Publisher(e1, "/robot/test", "std_msgs/String")
        p3 = Publisher(e1, "/robot/test2", "std_msgs/String")

        #  p.publish({"data": "Publisher {0}".format(p.id)})
        #  p2.publish({"data": "Publisher {0}".format(p2.id)})
        #  p3.publish({"data": "Publisher {0}".format(p3.id)})
        #  m.add(e1)
        while True:
            p.publish({"data": "Publisher {0}".format(p.id)})
            p2.publish({"data": "Publisher {0}".format(p2.id)})
            p3.publish({"data": "Publisher {0}".format(p3.id)})
            time.sleep(1)
    except KeyboardInterrupt as exc:
        print(exc)
        p.unregister()
        p2.unregister()
        p3.unregister()
        m.stop()
