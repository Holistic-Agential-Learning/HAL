#!/usr/bin/env python3.11
import random
import time
import bin.gui.GUI as GUI
import json
import sys
import subprocess
import os

if __name__ == "__main__":
    print("Running param_test...")
    f = open(sys.argv[1], "r")

    experiment = json.load(f)

    print(f"Received parameters for experiment '{experiment['NAME']}'")