import os
import sys

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import bin.lib.py_src.hal as hal
if __name__ == "__main__":
    print(hal.build_frequency_list(10, 0.25, 2))