#!/usr/bin/env python

from executor import ExecutorThreaded
from executor import ExecutorTornado
from executor import ExecutorManager

if __name__ == "__main__":
    try:
        m = ExecutorManager()
        m.start()
        #  e1 = ExecutorTornado(ip="127.0.0.1")
        #  e1.connect()
        #  m.add(e1)
        e2 = ExecutorThreaded(ip="127.0.0.1")
        e2.connect()
        m.add(e2)
    except KeyboardInterrupt as exc:
        print(exc)
        e1.stop()
