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

#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#

import time
import zmq

def sync():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5556")
    message = socket.recv()
    print(f"Received sync request: {message}")

    #  Send reply back to client
    socket.send(b"sync")

def thread_cpp():
    try:
        subprocess.run(["./bin/build/socket"])
    except KeyboardInterrupt:
        print("{__file__}: ^C signalled")
    except Exception as err:
        print(f"An error occurred: {err}")

def plot():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    
    # socket.subscribe("")
    socket.connect("tcp://localhost:5555")
    socket.setsockopt(zmq.SUBSCRIBE, b"")

    sync()

    buttons = []
    times = []
    stim_levels = []

    graph, = plt.plot([],[])
    plt.ylim(0,10)

    while True:
        #  Wait for next request from client
        try:
            print("waiting for message")
            message = socket.recv()
        except KeyboardInterrupt:
            break
        print(f"Received request: {message}")

        if (message == b"stop"):
            break

        b,t,s = message.decode("utf-8").split(";")
        print(f"{b},{t},{s}")

        times.append(int(t))
        stim_levels.append(int(s))
        print(times)
        print(stim_levels)

        graph.set_xdata(times)
        graph.set_ydata(stim_levels)
        plt.draw()
        print("plotting...")
        # graph = plt.plot(stim_levels, time,  color="g")[0]
        # plt.xlim(times[0], times[-1])
        
        # plt.scatter(stim_levels, times, 10, color="blue", label="Stimulation levels over time")
        # plt.show()
        print("done plotting")

        #  Do some 'work'

        #  Send reply back to client
        # socket.send(b"World")


# ready = False

# def thread_plot():
#     context = zmq.Context()
#     sock = context.socket(zmq.SUB)
#     sock.bind("tcp://*:5557")
#     print("complete")

#     while True:
#         try:
#             print("waiting for message...")
#             message = sock.recv()
#         except KeyboardInterrupt:
#             print("terminating thread due to interupt...")
#             break
#         except Exception:
#             print("unexpected error occurred")
#             break
            
#         print(f"received: {message}")
#         time.sleep(1)
#         if (message == "stop"):
#             break
    
#     sock.close()
#     context.term()
    

if __name__=="__main__":
    # plotter = threading.Thread(target = thread_cpp)

    # plotter.start()
    
    # time.sleep(1)

    plot()
    # plt.scatter([1, 2, 3, 4, 5, 6, 7, 8, 9], [0, 0, 0, 1, 2, 1, 0, 1, 0], 10, color="blue", label="Stimulation levels over time")
    # plt.show()

    # print("c++ script complete")
    # try:
    #     plotter.join()
    # except KeyboardInterrupt:
    #     print("Keyboard interrupt")
