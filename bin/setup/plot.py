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
    socket.connect("tcp://localhost:5555")
    socket.setsockopt(zmq.SUBSCRIBE, b"")

    sync()

    buttons = []
    times = []
    stim_levels = []

    fig = plt.gcf()
    fig.show()
    fig.canvas.draw()
    plt.ylim(-1,11)
    plt.pause(1)

    while True:
        #  Wait for next request from client
        try:
            message = socket.recv()
        except KeyboardInterrupt:
            break

        if (message == b"stop"):
            break

        b,t,s = message.decode("utf-8").split(";")

        times.append(int(t))
        stim_levels.append(int(s))
        buttons.append(b)

        plt.plot(stim_levels, times, color = 'g', marker = 'o')
        plt.pause(0.01)
        fig.canvas.draw()


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
