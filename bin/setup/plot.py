#!/usr/bin/env python
import time
import zmq

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import threading
import subprocess

def thread_plot():
    context = zmq.Context()
    sock = context.socket(zmq.REP)
    sock.bind("tcp://*:5555")

    while True:
        try:
            message = sock.recv()
        except KeyboardInterrupt:
            print("terminating thread due to interupt...")
            break
        except Exception:
            print("unexpected error occurred")
            break
            
        print(f"received: {message}")
        time.sleep(1)
        if (message == "stop"):
            break
    
    sock.close()
    context.term()
    

if __name__=="__main__":
    plotter = threading.Thread(target = thread_plot)

    plotter.start()

    try:
        subprocess.run(["./bin/build/socket"])
    except KeyboardInterrupt:
        print("{__file__}: ^C signalled")
    except Exception as err:
        print(f"An error occurred: {err}")

    plotter.join()
