import re
import os

def get_buttons(full_config, buttons, save_path):
    print(full_config)
    print(buttons)
    print(save_path)
    full_config_map = read_config_electrode_to_channel(full_config)
    buttons_data = [read_config(b) for b in buttons]

    for button in buttons_data:
        for data in button:
            try:
                data[0] = full_config_map[data[1]]
            except Exception as err:
                print(f"{data[1]} not routed")

    new_buttons = []

    for i in range(len(buttons)):
        new_path = save_path + "/" + os.path.basename(buttons[i])
        print(f"writing {new_path}")

        make_config(buttons_data[i], new_path)
        new_buttons.append(new_path)

    return new_buttons


    
    
def make_config(data, file_name):
    f = open(file_name, "w")

    to_write = ""

    for d in data:
        to_write += f"{d[0]}({d[1]}){d[2]}/{d[3]};"

    to_write += "\nH"

    f.write(to_write)

def read_config(file):
    # Error checking
    if (not file.endswith('.cfg')):
        return False


    f = open(file, "r")
    contents = f.read()

    # Parse file content
    electrode = 0
    x = 0
    y = 0
    channel = 0
    curr_word = ''
    electrode_map = {}

    channels = contents.split(";")
    channels.pop(len(channels) - 1)

    all_electrodes = []
    for channel_data in channels:
        data = re.split("\\(|\\)|/", channel_data)
        all_electrodes.append(data)


    return all_electrodes

def read_config_electrode_to_channel(file):
    data = read_config(file)

    electrodes = {}

    for channel_data in data:
        electrodes[channel_data[1]] = channel_data[0]

    return electrodes