#!/usr/bin/env python3.11
import PySimpleGUI as sg         
import os
import json
import re
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')
from datetime import date

w, h = sg.Window.get_screen_size()
sg.set_options(font=('bitstream charter', 18), element_padding=(6, 6), text_justification='left')

# NOTE: Stimulation names ~cannot~ have spaces in them
PROGRAMS_PATH = open("./bin/gui/programs.json", "r")
PROGRAMS = json.load(PROGRAMS_PATH)
    # "Print Bursts": {"exec": "print-bursts",
    #                 "stim_names": []},
    # "Stim Direction": {"exec": "stim-burst-direction",
    #                 "stim_names": ["General Stimulation"]},
    
START_MAXLAB = './start-maxlab.py'


CONFIG_PATH = '/home/mxwbio/configs'

### MAP EACH PARAM TO ITS FIELD/MIN/MAX
paramMap = {
    'NAME': (1,1),
    'NUM_PER_TRAIN': (1,20),
    'INTERVAL': (1,100), 
    'TRAIN_INTERVAL': (0.01, 10),
    'AMPLITUDE': (0, 1000),
    'NUM_TRAINS': (1,1000), 
    'PHASE': (100,1000),
    'DATE': (1,1),
    'FOLDER_NAME': (1,1),
    'E_SELECTED': (1,1)
}

PARAMETERS = ['NAME', 'FOLDER', 'DATE', '-PROGRAM-', 'PROGRAM_EXEC']

### CHECK IF PARAMETER IS IN VALID RANGE
def goodParam(value, param, valid):
    print("value: " + value)
    try:
        value = float(value)
        if (value < paramMap[param][0]) or (value > paramMap[param][1]):
            print(param + ' must be in range ' + str(paramMap[param][0]) + ' - ' + str(paramMap[param][1]))
            valid = False
        else:
            print(param, 'set to', value) 
    except:
        print(param, 'must be a number')
        valid = False
    return valid

def parseList(e_values, valid):
    e_values.replace(" ", "")
    try:
        # Split the string by commas and convert each part to an integer
        integers = [int(x) for x in e_values.split(',')]
        # Check if all elements are integers
        return all(isinstance(i, int) for i in integers) and valid
    except ValueError:
        # If any conversion fails, the input string is not a valid list of comma-separated integers
        return False

### VERIFY USER INPUT PARAMETERS
def saveParam(values):
    valid = True
    for param in values.keys():
        if(values[param] == ''):
            print(param + ' cannot be empty')
            valid = False
        # Check each integer parameter
        elif (param == 'E_SELECTED'):
            print(values[param])
        #    Make sure text box is a series of commas and numbers
            valid = parseList(values[param], valid)
        elif (param != 'NAME'): 
            valid = goodParam(values[param], param, valid)
    # Return tuple of valid and converted params
    return valid

def stim_param_in_range(param, value):
    try:
        value = float(value)
        if (value < paramMap[param][0]) or (value > paramMap[param][1]):
            return f'Must be in range {str(paramMap[param][0])} - {str(paramMap[param][1])}'
        else:
            return ''
    except:
        return 'Must be a number'

def check_stim_params(params):
    ret = {}
    valid = True
    for param in params.keys():
        if(params[param] == ''):
            ret[f"{param}_ERR"] = 'Cannot be empty'
            valid = False
        else:
            err = stim_param_in_range(param, params[param])
            ret[f"{param}_ERR"] = err
            if (err != ''):
                valid = False

    return (valid, ret)


def createFolder():
    # Create folder
    layout = [[sg.Text('Enter folder name:')],            
            [sg.InputText()],
            [sg.pin(sg.Text("Folder already exists!", text_color="red", visible=False, key="-FOLDER-ERR-"))],      
            [sg.Submit(key='Submit'), sg.Cancel(key='Cancel')]]            

    window = sg.Window('Create or Select Folder', layout)   
    while True:      
        event, values = window.read()     
        name = values[0]
        path = os.getcwd() + "/" + name
        # print(f"Path: {path}")
        if event == 'Submit':
            if (os.path.exists(path)):
                window["-FOLDER-ERR-"].update(visible=True)
            else:
                os.mkdir(name)
                window.close()
                return path
        
        if event == 'Cancel':
            window.close()
            return ''

def selectFolder():
    working_directory = os.curdir

    layout = [[sg.Text('Choose folder.')],            
            [sg.Input(key='Path'),
                sg.FolderBrowse(initial_folder=working_directory)],
            [sg.Submit(), sg.Cancel()]]             

    window = sg.Window('Create or Select Folder', layout)         
    event, values = window.read()        
    window.close()

    if event == 'Submit':
        name = values['Path']
        # sg.popup_ok("Folder at path " + name + " selected.") 
        window.close() 
        return name

    if event == 'Cancel':
        return ''

### CREATE/SELECT FOLDER WINDOWS:
def createSelectFolder():
    name = ""
    layout = [[sg.Text('Create folder or select existing folder?')],
                        [sg.Button('Create'), sg.Button('Select'), sg.Button('Cancel')]]

    window = sg.Window('Create or Select Folder', layout)        

    name = ''
    while (name == ''):
        event, values = window.read()
        if event == 'Cancel':
            break
        if event == 'Create': 
            name = createFolder()
        elif event == 'Select':
            name = selectFolder()
    window.close()
    return name



def save_file(values, is_config):
    full_folder_path = f"{values['FOLDER']}/{values['NAME']}"

    if not os.path.exists(full_folder_path):
        os.mkdir(full_folder_path)
    full_folder_path += f"/{values['CHIP_ID']}"
    if not os.path.exists(full_folder_path):
        os.mkdir(full_folder_path)

    fileName = values['NAME'] + ".json"
    values['FOLDER'] = full_folder_path

    print(f"Path: {full_folder_path}")
    
    f = open(values['FOLDER'] + "/" + fileName, "w")

    # write to JSON file
    
    # values['FOLDER_NAME'] = folderName
    if not is_config:
        values['PROGRAM_EXEC'] = PROGRAMS[values['-PROGRAM-']]['exec']
        if values['E_SELECTED'] != "":
            values['E_SELECTED'] = values['E_SELECTED'].replace(" ", "")
            values['E_SELECTED'] = [int(x) for x in values['E_SELECTED'].split(',')]
    # else:
    #     for well in values['WELLS']:
    #         configs[str(well)] = config

    # values['E_NUMS'] = electrode_nums 
    # values['E_COORDS'] = electrode_coords
    json.dump(values, f)
    f.close()

def select_stim(stims):
    layout = [[sg.Text("Select a stimulation to copy:")],
            [sg.ButtonMenu("Choose", ['Stim', list(stims.keys())], key='-CHOOSE-STIM-'),
                sg.Input(key='-STIM-')],
            [sg.pin(sg.Text("Invalid stimulation", text_color="red", key='-STIM-ERR-', visible=False))],
            [sg.Submit(), sg.Cancel()]]
    window = sg.Window("Choose Stimulation", layout, resizable=True, finalize=True)


    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            window.close()
            break
        elif event == 'Submit':
            if list(stims.keys()).count(values['-STIM-']) == 0:
                window['-STIM-ERR'].update(visible=True)
            else:
                window.close()
                return stims[values['-STIM-']]
        elif event == '-CHOOSE-STIM-':
            window['-STIM-'].update(value=values['-CHOOSE-STIM-'])
    
    return None


def check_curr_stims(stims, name):
    available_stims = {}
    for stim_name in stims:
        if stim_name != name:
            if stims[stim_name][0]:
                available_stims[stim_name] = stims[stim_name][1]
    
    return available_stims

def get_exp_stims():
    params = choose_exp(False)

    return params['STIMULATIONS']


def import_stimulation(stims, name, prev_values):
    layout = [[sg.Text("Would you like to copy a stimulation from this experiment or another?")],
            [sg.Button("This experiment"), sg.Button("Another experiment"), sg.Cancel()]]
    
    window = sg.Window("Copy Stimulation", layout, resizable=True, finalize=True)
    available_curr_stims = check_curr_stims(stims, name)

    if (available_curr_stims == {}):
        window['This experiment'].update(disabled=True)
    
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            window.close()
            break
        elif event == 'This experiment':
            window.close()
            return select_stim(available_curr_stims)
        elif event == 'Another experiment':
            window.close()
            available_stims = get_exp_stims()
            if not available_stims:
                break
            else:
                return select_stim(available_stims)
    
    return None
            

def edit_stimulation(stims, name, prev_values):
    layout = [[sg.Text(name)],
            [sg.Text('Parameters', font=("Helvetica", 12, "bold"))],
            [[sg.Text('Number of pulses per train:'), sg.InputText(key='NUM_PER_TRAIN', size=(6,1)), sg.Text('(1 - 20)')],
            [sg.pin(sg.Text('Error', text_color='red', visible=False, key='NUM_PER_TRAIN_ERR'))]],
            [[sg.Text('Pulse interval [ms]:'), sg.InputText(key='INTERVAL', size=(6,1)), sg.Text('(1ms - 100ms)')],
            [sg.pin(sg.Text('Error', text_color='red', visible=False, key='INTERVAL_ERR'))]],
            [[sg.Text('Number of pulse trains:'), sg.InputText(key='NUM_TRAINS', size=(6,1)), sg.Text('(1 - 1000)')],
            [sg.pin(sg.Text('Error', text_color='red', visible=False, key='NUM_TRAINS_ERR'))]],
            [[sg.Text('Pulse train interval [s]:'), sg.InputText(key='TRAIN_INTERVAL', size=(6,1)), sg.Text('(0.01s - 10s)')],
            [sg.pin(sg.Text('Error', text_color='red', visible=False, key='TRAIN_INTERVAL_ERR'))]],
            [[sg.Text('Amplitude:'), sg.InputText(key='AMPLITUDE', size=(6,1)), sg.Text('(0mV - 1000mV)')],
            [sg.pin(sg.Text('Error', text_color='red', visible=False, key='AMPLITUDE_ERR'))]],
            [[sg.Text('Stimulation pulse phase [µs]:'), sg.InputText(key='PHASE', size=(6,1)), sg.Text('(100µs - 1000µs)')],
            [sg.pin(sg.Text('Error', text_color='red', visible=False, key='PHASE_ERR'))]], 
            [sg.Button('Save'), sg.Button('Import Stimulation'), sg.Button('Cancel')]]
    window = sg.Window("Edit Stimulation", layout, resizable=True, finalize=True)
    if prev_values != None:
        for key in prev_values.keys():
            window[key].update(value=prev_values[key])
    ret = None
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            if (prev_values != None):
                ret = prev_values
            window.close()
            break
        elif event == 'Import Stimulation':
            stim = import_stimulation(stims, name, prev_values)
            if stim:
                for param in stim:
                    window[param].update(value=stim[param])
        elif event == 'Save':
            valid, errs = check_stim_params(values)
            if (valid):
                window.close()
                ret = values
                break
            for name in errs.keys():
                if errs[name] == '':
                    window[name].update(visible=False)
                else:
                    window[name].update(value=errs[name], visible=True)

    return ret

def view_well_config(window, values, well):
    if values[f'-CONFIG-{well}-']:
        if (read_config(values[f'-CONFIG-{well}-'], True)):
            window[f'-CONFIG-ERR-{well}'].update(visible=False)
        else:
            window[f'-CONFIG-ERR-{well}'].update(visible=True, value="Not a valid config")
    else:
        window[f'-CONFIG-ERR-{well}'].update(visible=True, value="Config not selected")

def edit_wells(prev_values):
    layout = [[sg.Text("Select wells and corresponding config files.")],
                [[sg.Checkbox("0", key="0"), sg.Input(key='-CONFIG-0-'),
                        sg.FileBrowse(initial_folder=CONFIG_PATH), 
                        sg.Button("View", key="View-0")], 
                        [sg.pin(sg.Text("Invalid Config", text_color="red", visible=False, key='-CONFIG-ERR-0'))]],
                [[sg.Checkbox("1", key="1"), sg.Input(key='-CONFIG-1-'),
                        sg.FileBrowse(initial_folder=CONFIG_PATH), 
                        sg.Button("View", key="View-1")], 
                        [sg.pin(sg.Text("Invalid Config", text_color="red", visible=False, key='-CONFIG-ERR-1'))]],
                
                [[sg.Checkbox("2", key="2"), sg.Input(key='-CONFIG-2-'),
                        sg.FileBrowse(initial_folder=CONFIG_PATH), 
                        sg.Button("View", key="View-2")], 
                        [sg.pin(sg.Text("Invalid Config", text_color="red", visible=False, key='-CONFIG-ERR-2'))]],
                
                [[sg.Checkbox("3", key="3"), sg.Input(key='-CONFIG-3-'),
                        sg.FileBrowse(initial_folder=CONFIG_PATH), 
                        sg.Button("View", key="View-3")], 
                        [sg.pin(sg.Text("Invalid Config", text_color="red", visible=False, key='-CONFIG-ERR-3'))]],
                
                [[sg.Checkbox("4", key="4"), sg.Input(key='-CONFIG-4-'),
                        sg.FileBrowse(initial_folder=CONFIG_PATH), 
                        sg.Button("View", key="View-4")], 
                        [sg.pin(sg.Text("Invalid Config", text_color="red", visible=False, key='-CONFIG-ERR-4'))]],
                
                [[sg.Checkbox("5", key="5"), sg.Input(key='-CONFIG-5-'),
                        sg.FileBrowse(initial_folder=CONFIG_PATH), 
                        sg.Button("View", key="View-5")], 
                        [sg.pin(sg.Text("Invalid Config", text_color="red", visible=False, key='-CONFIG-ERR-5'))]],
                [sg.pin(sg.Text("Select at least one well", text_color="red", visible=False, key='-WELLS-ERR-'))],
                [sg.Submit(), sg.Cancel()]]

    window = sg.Window("Add Wells", layout, resizable=True, finalize=True)
    ret = None
    if prev_values != None:
        ret = prev_values
        for key in prev_values.keys():
            window[key].update(value=prev_values[key])

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            ret = prev_values
            window.close()
            break
        elif event == '-ALL-WELLS-':
            if values['-ALL-WELLS-'] == True:
                for i in range(6):  
                    window[str(i)].update(value=True)
            ret = values
        elif event == 'Submit':
            selected = False
            for i in range(6):
                selected = values[str(i)] or selected
            if selected:
                valid = True
                for i in range(6):
                    if values[str(i)]:
                        if (read_config(values[f'-CONFIG-{i}-'], False)):
                            window[f'-CONFIG-ERR-{i}'].update(visible=False)
                        else:
                            valid = False
                            window[f'-CONFIG-ERR-{i}'].update(visible=True)
                if valid:
                    ret = values
                    window.close()
                    break
            else:
                window['-WELLS-ERR-'].update(visible=True)
        else:
            for i in range(6):
                if event == f"View-{i}":
                    view_well_config(window, values, i)
    
    return ret

# [sg.Text('List of electrodes to stimulate:'), sg.InputText(key='E_SELECTED', size=(30,1))]

def get_stimulation_button(program, name):
    layout = [[sg.pin(sg.Text(name, visible=False, key=f"-{program}-{name}-")), sg.pin(sg.Button("Edit", key=('-EDIT-STIM-', program, name), visible=False)), sg.Text('Verified', text_color="green", key=f'-{program}-{name}-VERIFIED-', visible=False)],
                [sg.pin(sg.Text("Invalid stimulation parameters", visible=False, text_color="red", key=f"-{program}-{name}-ERR-"))]]
    return layout

def make_edit_stimulations(window):
    for program in PROGRAMS.keys():
        stim_names = PROGRAMS[program]["stim_names"]
        for name in stim_names:
            stim = get_stimulation_button(program, name)
            window.extend_layout(window["-STIMULATIONS-"], stim)
    
    stim_e = [[sg.pin(sg.Text('List of electrodes to stimulate:', key="-STIM-ELECT-", visible=False)), sg.pin(sg.InputText(key='E_SELECTED', size=(30,1), visible=False))],
                            [sg.pin(sg.Text("", text_color="red", visible=False, key="-E_SELECTED-ERR-"))]]
    window.extend_layout(window["-STIMULATIONS-"], stim_e)
    # window['-STIMULATIONS-'].update(scrollable=True)

def get_edit_parameter(program, param_name):
    layout = [[sg.pin(sg.Text(f"{param_name}:", visible=False, key=f"-{program}-{param_name}-TEXT-")), sg.pin(sg.Input(key=f'-{program}-{param_name}-', visible=False))]]
    return layout

def make_parameters(window):
    for program in PROGRAMS.keys():
        parameters = PROGRAMS[program]["parameters"]
        for param in parameters.keys():
            param_layout = get_edit_parameter(program, param)
            window.extend_layout(window["-PARAMETERS-"], param_layout)

def define_exp_window(old_exp):
    message = 'Create a new experiment'
    window_message = 'New Experiment'
    if old_exp:
        message = 'Modify an experiment'
        window_message = 'Modify Experiment'

    layout = [[sg.Text(message, font=("Helvetica", 16, "bold"))],
            [[sg.Text('Experiment name:'), sg.InputText(key='NAME', size=(40,1))]],
            [sg.pin(sg.Text("Invalid name", text_color="red", visible=False, key='-NAME-ERR-'))],
            [[sg.Text('Chip ID: '), sg.Input(key='CHIP_ID')]],
            [sg.pin(sg.Text('Chip ID: ', text_color="red", visible=False, key='-CHIP_ID-ERR-'))],
            [[sg.Text("Create or select folder: ")], [sg.Input(key='FOLDER'), sg.Button('Create'), sg.Button('Select')],
            [sg.pin(sg.Text("Please select or create a folder", text_color="red", visible=False, key='-FOLDER-ERR-'))]],
            [[sg.Checkbox('', key='-MAXONE-', enable_events=True, default=True, disabled=True), 
                sg.Text("MaxOne               "),
                sg.Checkbox('', enable_events=True, key='-MAXTWO-'),
                sg.Text("MaxTwo")]],
            [sg.pin(sg.Col([[sg.Text('Choose an electrode configuration file.')],            
                        [sg.Input(key='-CONFIG-'),
                        sg.FileBrowse(initial_folder=CONFIG_PATH), 
                        sg.Button("View")], 
                        [sg.pin(sg.Text("Invalid Config", text_color="red", visible=False, key='-CONFIG-ERR-'))]], key='-CONFIG-COL-'))],
            [sg.pin(sg.Col([[sg.Text('Choose recording wells:'), sg.Button("Choose", key='-CHOOSE-WELLS-'), 
            sg.Text("Selected", text_color="green", visible=False, key='-SELECTED-WELLS-')],
            [sg.pin(sg.Text("Select at least one well", text_color="red", visible=False, key='-WELLS-ERR-'))]], 
            visible=False, key='-WELLS-COL-'))],
            [[sg.Text('Choose a program:')],
                [sg.ButtonMenu("Choose", ['Program', list(PROGRAMS.keys())], key='-CHOOSE-PROGRAM-'),
                sg.Input(key='-PROGRAM-')],
                sg.pin(sg.Text("Choose a program", text_color="red", visible=False, k='-PROGRAM-ERR-'))],
            [sg.pin(sg.Column([[sg.Text("Parameters:", visible=False, key='-PARAM-TEXT-')]], k='-PARAMETERS-'))],
            [sg.pin(sg.Column([[sg.Text("Stimulations", visible=False, key='-STIM-TEXT-')]], k='-STIMULATIONS-'))], 
            [sg.Button('Save experiment'), sg.Button('Cancel')]]
    # layout = [[sg.Col([[sg.Text(message, font=("Helvetica", 16, "bold"))],
    #         [sg.Text('Experiment name:'), sg.InputText(key='NAME', size=(40,1))],
    #             [sg.pin(sg.Text("Invalid name", text_color="red", visible=False, key='-NAME-ERR-'))],
    #         [sg.Text("Create or select folder: "), sg.Input(key='FOLDER'), sg.Button('Create'), sg.Button('Select'),
    #         sg.pin(sg.Text("Please select or create a folder", text_color="red", visible=False, key='-FOLDER-ERR-'))],
    #         [sg.Checkbox('', key='-MAXONE-', enable_events=True, default=True, disabled=True), 
    #             sg.Text("MaxOne               "),
    #             sg.Checkbox('', enable_events=True, key='-MAXTWO-'),
    #             sg.Text("MaxTwo")],
    #         [sg.pin(sg.Col([[sg.Text('Choose an electrode configuration file.')],            
    #                     [sg.Input(key='-CONFIG-'),
    #                     sg.FileBrowse(initial_folder='/Users/Trevor/Documents/Halligan/Hybrot/configs'), 
    #                     sg.Button("View")], 
    #                     [sg.pin(sg.Text("Invalid Config", text_color="red", visible=False, key='-CONFIG-ERR-'))]], key='-CONFIG-COL-'))],
    #         [sg.pin(sg.Col([[sg.Text('Choose recording wells:'), sg.Button("Choose", key='-CHOOSE-WELLS-'), 
    #         sg.Text("Selected", text_color="green", visible=False, key='-SELECTED-WELLS-')],
    #         [sg.pin(sg.Text("Select at least one well", text_color="red", visible=False, key='-WELLS-ERR-'))]], 
    #         visible=False, key='-WELLS-COL-'))],
    #         [sg.Text('Choose a program:'),
    #             sg.ButtonMenu("Choose", ['Program', list(PROGRAMS.keys())], key='-CHOOSE-PROGRAM-'),
    #             sg.Input(key='-PROGRAM-')],
    #             [sg.pin(sg.Text("Choose a program", text_color="red", visible=False, k='-PROGRAM-ERR-'))],
    #         [sg.pin(sg.Column([[sg.Text("Parameters:", visible=False, key='-PARAM-TEXT-')]], k='-PARAMETERS-'))],
    #         [sg.pin(sg.Column([[sg.Text("Stimulations:", visible=False, key='-STIM-TEXT-')]], k='-STIMULATIONS-'))], 
    #         [sg.Button('Save experiment'), sg.Button('Cancel')]], scrollable=True, vertical_scroll_only=True, expand_y=True, expand_x=True)]]
    # , scrollable=True, vertical_scroll_only=True
    window = sg.Window(window_message, layout, resizable=True, finalize=True, location=(int(w/4), 0))

    
    make_edit_stimulations(window)
    make_parameters(window)
    return window

def program_visibility(window, program, visible):
    stim_names = PROGRAMS[program]["stim_names"]
    parameters = PROGRAMS[program]["parameters"]
    for name in stim_names:
        window[f'-{program}-{name}-'].update(visible=visible)
        window[('-EDIT-STIM-', program, name)].update(visible=visible)
        if not visible:
            window[f'-{program}-{name}-VERIFIED-'].update(visible=visible)
            window[f'-{program}-{name}-ERR-'].update(visible=visible)

    for param in parameters.keys():
        window[f"-{program}-{param}-TEXT-"].update(visible=visible)
        window[f"-{program}-{param}-"].update(visible=visible)
        
    if len(stim_names) > 0:
        window["-STIM-ELECT-"].update(visible=visible)
        window["E_SELECTED"].update(visible=visible)

def define_exp(old_experiment):
    window = define_exp_window(old_experiment)
    experiment_ready = False
    program = ''
    params = {}
    wells = None
    system = 1
    if old_experiment:
        if old_experiment['STIMULATIONS'] != None:
            stimulations = old_experiment['STIMULATIONS']
            for name in stimulations:
                params[name] = (True, stimulations[name])
        old_experiment.pop('DATE')
        old_experiment.pop('Browse')
        old_experiment.pop('STIMULATIONS')
        old_experiment.pop('PROGRAM_EXEC')
        old_experiment.pop('-CHOOSE-PROGRAM-')
        program = old_experiment['-PROGRAM-']
        old_experiment.pop('-SCRIPT-')
        for param in PROGRAMS[program]["parameters"].keys():
            window[f"-{program}-{param}-"].update(value=old_experiment[param])
            old_experiment.pop(param)
        if old_experiment['-MAXTWO-']:
            window['-WELLS-COL-'].update(visible=True)
            window['-MAXTWO-'].update(disabled=True)
            window['-MAXONE-'].update(value=False, disabled=False)
            window['-CONFIG-COL-'].update(visible=False)
            wells = {}
            wells_list = old_experiment['WELLS']
            for i in range(6):
                if (wells_list.count(i) == 1):
                    wells[str(i)] = True
                else:
                    wells[str(i)] = False
            for well in wells_list:
                wells[f'-CONFIG-{well}-'] = old_experiment["CONFIGS"][str(well)]["PATH"]

        elif old_experiment['-MAXONE-']:
            window['-WELLS-COL-'].update(visible=False)
            window['-MAXONE-'].update(disabled=True)
            window['-MAXTWO-'].update(value=False, disabled=False)
            config_path = old_experiment['CONFIGS']['0']['PATH']
            window['-CONFIG-'].update(value=config_path)
        old_experiment.pop('CONFIGS')
        old_experiment.pop('WELLS')

        old_name = old_experiment["NAME"]
        old_chipid = old_experiment["CHIP_ID"]
        old_folder = old_experiment['FOLDER']
        new_folder = old_folder.removesuffix(f"/{old_name}/{old_chipid}")

        old_experiment['FOLDER'] = new_folder

        if old_experiment['E_SELECTED'] != None:
            old_experiment['E_SELECTED'] = ", ".join(str(elec) for elec in old_experiment['E_SELECTED'])
        for param in old_experiment:
            window[param].update(value=old_experiment[param])
        program_visibility(window, program, True)
        for stim in PROGRAMS[program]["stim_names"]:
            window[f'-{program}-{stim}-VERIFIED-'].update(visible=True)
    experiment = None
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        window.refresh()
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            window.close()
            break

        elif event == '-CHOOSE-PROGRAM-':
            if program != '':
                
                program_visibility(window, program, False)

                # stimulation parameters
                params = {}
            
            program = values['-CHOOSE-PROGRAM-']
            if PROGRAMS[program]["stim_names"] != []:
                window['-STIM-TEXT-'].update(visible=True)
            if PROGRAMS[program]["parameters"] != {}:
                window['-PARAM-TEXT-'].update(visible=True)
            program_visibility(window, program, True)
            
            window['-PROGRAM-'].update(program)
            for name in PROGRAMS[program]["stim_names"]:
                    params[name] = (False, None)
        elif event == "View":
            if values['-CONFIG-']:
                if (read_config(values['-CONFIG-'], True)):
                    window['-CONFIG-ERR-'].update(visible=False)
                else:
                    window['-CONFIG-ERR-'].update(visible=True, value="Not a valid config")
            else:
                window['-CONFIG-ERR-'].update(visible=True, value="Config not selected")
        elif event == 'Create':
            folder = createFolder()
            window['FOLDER'].update(folder)
        elif event == 'Select':
            folder = selectFolder()
            window['FOLDER'].update(folder)
        elif event == '-MAXONE-':
            window['-CONFIG-COL-'].update(visible=True)
            window['-WELLS-COL-'].update(visible=False)
            window['-MAXONE-'].update(disabled=True)
            window['-MAXTWO-'].update(value=False, disabled=False)
        elif event == '-MAXTWO-':
            window['-CONFIG-COL-'].update(visible=False)
            window['-WELLS-COL-'].update(visible=True)
            window['-MAXTWO-'].update(disabled=True)
            window['-MAXONE-'].update(value=False, disabled=False)
        elif event == '-CHOOSE-WELLS-':
            wells = edit_wells(wells)
            if wells != None:
                keys = list(wells.keys())
                for key in keys:
                    if key[0] == "B":
                        wells.pop(key)
                window['-SELECTED-WELLS-'].update(visible=True)
            else:
                
                window['-SELECTED-WELLS-'].update(visible=False)
        elif event[0] == '-EDIT-STIM-':
            name = event[2]
            values = edit_stimulation(params, name, params[name][1])
            if values == None:
                params[name] = (False, values)
                window[f'-{program}-{name}-VERIFIED-'].update(visible=False)
            else:
                params[name] = (True, values)
                window[f'-{program}-{name}-VERIFIED-'].update(visible=True)
            
        else:
            # Attempt save experiment
            
            valid = True
            if program == '':
                valid = False
                window['-PROGRAM-ERR-'].update(visible=True)
            else:
                window['-PROGRAM-ERR-'].update(visible=False)
            for key in values.keys():
                if (key == "NAME"):
                    if (values[key] == ''):
                        valid = False
                        window["-NAME-ERR-"].update(visible=True)
                    else:
                        window["-NAME-ERR-"].update(visible=False)
                elif key == 'CHIP_ID':
                    if values[key] == '':
                        valid = False
                        window["-CHIP_ID-ERR-"].update(visible=True)
                    else:
                         window["-CHIP_ID-ERR-"].update(visible=False)
                elif key == 'FOLDER':
                    if (values[key] == ''):
                        valid = False
                        window["-FOLDER-ERR-"].update(visible=True)
                    else:
                        window["-FOLDER-ERR-"].update(visible=False)
                        
                elif key == "-MAXONE-":
                    # if values['-CONFIG-'] != None:
                    if values[key]:
                        if (read_config(values['-CONFIG-'], False)):
                            window['-CONFIG-ERR-'].update(visible=False)
                        else:
                            valid = False
                            window['-CONFIG-ERR-'].update(visible=True)
                elif key == "-MAXTWO-":
                    if values[key]:
                        if wells == None:
                            valid = False
                            window['-WELLS-ERR-'].update(visible=True)
                        else:
                            window['-WELLS-ERR-'].update(visible=False)
                        
                elif key == "E_SELECTED":
                    if program != '':
                        window['-PROGRAM-ERR-'].update(visible=False)
                        if len(PROGRAMS[program]['stim_names']) > 0: 
                            if values[key] == '':
                                valid = False
                                window['-E_SELECTED-ERR-'].update(visible=True, value="Invalid stimulation electrodes")
                    else:
                        valid = False
                        window['-PROGRAM-ERR-'].update(visible=True)
                
            for name in params.keys():
                if (params[name][0]):
                    window[f"-{program}-{name}-ERR-"].update(visible=False)
                else:
                    valid = False
                    window[f"-{program}-{name}-ERR-"].update(visible=True)
            # if saveExp(values, params, program):y 
            #     break
            if (valid):
                for stim in PROGRAMS[program]['stim_names']:
                    # print(f'params! {params[stim]}')
                    params[stim] = params[stim][1]
                values["STIMULATIONS"] = params
                for p in PROGRAMS.keys():
                    for param in PROGRAMS[p]["parameters"].keys():
                        if p == program:
                            values[param] = values[f"-{p}-{param}-"]
                        values.pop(f"-{p}-{param}-")

                experiment = values
                experiment['-SCRIPT-'] = START_MAXLAB
                today = date.today()
                date_str = today.strftime("%m/%d/%y")
                values['DATE'] = date_str
                
                configs = {}
                if wells != None:
                    wells_list = []
                    for i in range(6):
                        if (wells[str(i)]):
                            wells_list.append(i)
                    experiment['WELLS'] = wells_list
                    for well in wells_list:
                        val, electrode_nums, electrode_coords = read_config(wells[f'-CONFIG-{well}-'], False)
                        config = {}
                        config['PATH'] = wells[f'-CONFIG-{well}-']
                        config['E_NUMS'] = electrode_nums
                        config['E_COORDS'] = electrode_coords
                        configs[str(well)] = config
                else:
                    val, electrode_nums, electrode_coords = read_config(experiment['-CONFIG-'], False)
                    config = {}
                    config['PATH'] = experiment['-CONFIG-']
                    config['E_NUMS'] = electrode_nums
                    config['E_COORDS'] = electrode_coords
                    configs['0'] = config
                    experiment['WELLS'] = [0]
                experiment['CONFIGS'] = configs
                print(f"saving script {START_MAXLAB}...")
                save_file(experiment, False)
                window.close()
                return run_or_modify(experiment, f"Experiment '{experiment['NAME']}' has been saved successfully.")

    return experiment

def check_def_exp_params(values, stim_params, program):
    print("hi")
    # errs = {}
    # for key in values.keys():
    #     if (key == "NAMES"):
    #         if (values[key] == ''):
    #             errs[]

def saveExp(values, stim_params, program):
    errs = check_def_exp_params(values, stim_params, program)
    if errs:
        folderName = createSelectFolder()
        if (folderName == ''):
            print("Parameters not saved")
        elif (folderName != ''):
            values['E_NUMS'] = electrode_nums
            values['E_COORDS'] = electrode_coords
            # Verify that parameters saved 
            print("Parameters saved in folder " + folderName)
            return True
        else: 
            print("Parameters not saved")
    return False

# def saveParam(values):
#     valid = True
#     for param in values.keys():
#         if(values[param] == ''):
#             print(param + ' cannot be empty')
#             valid = False
#         # Check each integer parameter
#         elif (param == 'E_SELECTED'):
#             print(values[param])
#         #    Make sure text box is a series of commas and numbers
#             valid = parseList(values[param], valid)
#         elif (param != 'NAME'): 
#             valid = goodParam(values[param], param, valid)
#     # Return tuple of valid and converted params
#     return valid


# [sg.Text('CHIP ID:'), sg.InputText(key='CHIP_ID')],
# valid_id = valid_chip_id(values['CHIP_ID'])
def run(experiment):
    layout = [[sg.Text('Chip ID:'), sg.InputText(key='CHIP_ID')],
            [sg.pin(sg.Text("", text_color="red", key="-CHIP-ID-ERR-", visible=False))],
            [sg.Text('Trial Name:'), sg.InputText(key='TRIAL_NAME')],
            [sg.pin(sg.Text("Invalid trial name", text_color="red", key="-TRIAL-NAME-ERR-", visible=False))],
            [sg.Button("Run"), sg.Cancel()]]
    
    window = sg.Window(f"Run {experiment['NAME']}", layout, finalize=True, resizable=True)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            window.close()
            break
        elif event == "Run":
            valid_params = True
            for param in values:
                if param == "CHIP_ID":
                    valid_chip = True
                    try:
                        int(values[param])
                        if not (len(values[param]) == 5):
                            valid_chip = False
                            window['-CHIP-ID-ERR-'].update(visible=True, value="Chip ID must be 5 digits")
                    except:
                        valid_chip = False
                        window['-CHIP-ID-ERR-'].update(visible=True, value="Chip ID must be a number")
                    if valid_chip:
                        window['-CHIP-ID-ERR-'].update(visible=False)
                    valid_params = valid_params and valid_chip
                elif param == "TRIAL_NAME":
                    if values[param] == '':
                        valid_params = False
                        window['-TRIAL-NAME-ERR-'].update(visible=True)
                    else:
                        window['-TRIAL-NAME-ERR-'].update(visible=False)

            if valid_params:
                window.close()
                experiment['CHIP_ID'] = values['CHIP_ID']
                experiment['TRIAL_NAME'] = values['TRIAL_NAME']
                return experiment
            
    return None

def run_or_modify(experiment, message):
    layout = [[sg.Text(message)],
            [sg.Button("Run"), sg.Button("Modify"), sg.Button("Exit")]]
    window = sg.Window(experiment["NAME"], layout, finalize=True, resizable=True)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit': # if user closes window or clicks cancel
            window.close()
            break
        elif event == "Run":
            window.close()
            print("returning string!")
            return f"{experiment['FOLDER']}/{experiment['NAME']}.json"
        elif event == "Modify":
            window.close()
            return define_exp(experiment)
    
    return None

def choose_exp(run):
    working_directory = os.curdir

    layout = [[sg.Text('Choose experiment file.')],            
            [sg.Input(key='EXP_PROTOCOL'),
                sg.FileBrowse(initial_folder=working_directory)],
            [sg.pin(sg.Text("Invalid experiment file", text_color="red", visible=False, key='-FILE-ERR-'))],
            [sg.Submit(), sg.Cancel()]]             

    window = sg.Window('Choose Experiment', layout, finalize=True, resizable=True)
            

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            window.close()
            break
        elif event == 'Submit':
            fileName = values['EXP_PROTOCOL']
            f = open(fileName, "r")

            # Read in data
            # try:
            parameters = json.load(f)
            valid = True
            for param in PARAMETERS:
                if parameters[param] == None:
                    valid = False
                    window['-FILE-ERR-'].update(visible=True)
            if (valid):
                window.close()
                if run:
                    parameters['-SCRIPT-'] = START_MAXLAB
                    return run_or_modify(parameters, f"Experiment '{parameters['NAME']}' has been chosen.")
                else:
                    return parameters

            # except:
                # window['-FILE-ERR-'].update(visible=True)

    return None

def valid_chip_id(chip_num):
    length = len(chip_num)
    try:
        value = int(chip_num)
        valid_id = (length == 5)
        if (not valid_id):
            print("CHIP ID must be 5 digits.")
        return valid_id
    except:
        print("CHIP ID must be an integer.")
        return False

# Purpose: Draw the figure on the PySimpleGUI canvas. 
# Return: The canvas with the given figure drawn on it. 
def draw_figure(canvas, figure):
        figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side="top", fill="both", expand=1)
        return figure_canvas_agg

# Purpose: Display the config on the confirmation window.
# Return: True or False, depending on if the user confirms their choice. 
def display_config(electrode_coords):
    # Set all active electrodes to 1
    vals = np.zeros((120,220))
    for (x, y) in electrode_coords: 
        vals[int(y/17.5),int(x/17.5)] = 1


    # Set up the window for the configuration display
    layout = [[sg.Button('Ok')],
                        [sg.Canvas(size=(500,400), key='CANVAS')],
                        [sg.Text('Active electrodes are highlighted in yellow.')]
                        ]
	
	# width and height used to be divided by 4
    window = sg.Window('Electrode Configuration', layout, size=(w,h), 
        finalize=True, element_justification='center')

    # Display the configuration
    fig = matplotlib.figure.Figure(figsize=(50,40), dpi=100)
    fig.add_subplot(111).imshow(vals, cmap='cividis')
    draw_figure(window['CANVAS'].TKCanvas, fig)
    event, values = window.read()

    if (event == 'Ok' or event == sg.WIN_CLOSED):
        window.close()
        return True


# Purpose: Parse through the config file. 
# Return: Returns true if the file was read successfully. Returns false
#     if the file was an incorrect file type (not .cfg) or if the user wants 
#     to choose a new file. 
def read_config(file, display):
    # Error checking
    if (not file.endswith('.cfg')):
        return False


    f = open(file, "r")
    contents = f.read()

    # Parse file content
    electrode_nums = []
    x = []
    y = []
    curr_word = ''
    for char in contents:
        if (char == '('):
            curr_word = ''
        elif (char == ')'):
            electrode_nums.append(int(curr_word))
            curr_word = ''
        elif (char == '/'):
            x.append(float(curr_word))
            curr_word = ''
        elif (char == ';'):
            y.append(float(curr_word))
            curr_word = ''
        elif (char == 'H'):
            break
        else:
            curr_word = curr_word + char
    
    electrode_coords = list(zip(x,y))

    if (display):
        display_config(electrode_coords)

    return (True, electrode_nums, electrode_coords)

# Purpose: Window to allow user to select the electrode configuration they want.
def chooseConfig():
    layout = [[[sg.Text('Choose an electrode configuration file.')],            
                        [sg.Input(key='CONFIG'),
                        sg.FileBrowse(initial_folder='../Configs')]],
                        [sg.Button('Cancel'), sg.Button('Continue')]]
    window = sg.Window('Electrode Configuration', layout)
    event, values = window.read()

    while True:
        if (event == 'Cancel'):
            window.close()
            return ([],[])
        if (event=='Continue'):
            (valid_config, electrode_nums, electrode_coords) = read_config(values['CONFIG'])
            if (not valid_config):
                print('Please choose a new configuration file with extension .cfg.')
                event, values = window.read()
            elif (valid_config):
                window.close()
                return (electrode_nums, electrode_coords)


def runExp(experiment):
    print("run experiment!")

def get_config():
    wells = None
    layout = [[[sg.Text('Experiment name:'), sg.InputText(key='NAME', size=(40,1))]],
                [sg.pin(sg.Text("Invalid name", text_color="red", visible=False, key='-NAME-ERR-'))],
                [sg.Text("Choose a Python startup script.")], 
                    [sg.Input(key='-SCRIPT-'),
                        sg.FileBrowse(initial_folder='./bin')], 
                [sg.pin(sg.Text("Please select a Python script", key="-SCRIPT-ERR-", text_color="red", visible=False))], 
            [[sg.Text("Create or select folder: ")], [sg.Input(key='FOLDER'), sg.Button('Create'), sg.Button('Select')],
            [sg.pin(sg.Text("Please select or create a folder", text_color="red", visible=False, key='-FOLDER-ERR-'))]],
            [[sg.Checkbox('', key='-MAXONE-', enable_events=True, default=True, disabled=True), 
                sg.Text("MaxOne               "),
                sg.Checkbox('', enable_events=True, key='-MAXTWO-'),
                sg.Text("MaxTwo")]],
            [sg.pin(sg.Col([[sg.Text('Choose an electrode configuration file.')],            
                        [sg.Input(key='-CONFIG-'),
                        sg.FileBrowse(initial_folder=CONFIG_PATH), 
                        sg.Button("View")], 
                        [sg.pin(sg.Text("Invalid Config", text_color="red", visible=False, key='-CONFIG-ERR-'))]], key='-CONFIG-COL-'))],
            [sg.pin(sg.Col([[sg.Text('Choose recording wells:'), sg.Button("Choose", key='-CHOOSE-WELLS-'), 
            sg.Text("Selected", text_color="green", visible=False, key='-SELECTED-WELLS-')],
            [sg.pin(sg.Text("Select at least one well", text_color="red", visible=False, key='-WELLS-ERR-'))]], 
            visible=False, key='-WELLS-COL-'))],
            [sg.Button("Submit and Run"), sg.Button("Cancel")]]
    
    window = sg.Window("Select Config", layout, resizable=True, finalize=True)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            window.close()
            break
            
        elif event == "View":
            if values['-CONFIG-']:
                if (read_config(values['-CONFIG-'], True)):
                    window['-CONFIG-ERR-'].update(visible=False)
                else:
                    window['-CONFIG-ERR-'].update(visible=True, value="Not a valid config")
            else:
                window['-CONFIG-ERR-'].update(visible=True, value="Config not selected")
        elif event == 'Create':
            folder = createFolder()
            window['FOLDER'].update(folder)
        elif event == 'Select':
            folder = selectFolder()
            window['FOLDER'].update(folder)
        elif event == '-MAXONE-':
            window['-CONFIG-COL-'].update(visible=True)
            window['-WELLS-COL-'].update(visible=False)
            window['-MAXONE-'].update(disabled=True)
            window['-MAXTWO-'].update(value=False, disabled=False)
        elif event == '-MAXTWO-':
            window['-CONFIG-COL-'].update(visible=False)
            window['-WELLS-COL-'].update(visible=True)
            window['-MAXTWO-'].update(disabled=True)
            window['-MAXONE-'].update(value=False, disabled=False)
        elif event == '-CHOOSE-WELLS-':
            wells = edit_wells(wells)
            if wells != None:
                keys = list(wells.keys())
                for key in keys:
                    if key[0] == "B":
                        wells.pop(key)
                window['-SELECTED-WELLS-'].update(visible=True)
            else:
                
                window['-SELECTED-WELLS-'].update(visible=False)
        else:

            valid = True

            for key in values.keys():
                if (key == "NAME"):
                    if (values[key] == ''):
                        valid = False
                        window["-NAME-ERR-"].update(visible=True)
                    else:
                        window["-NAME-ERR-"].update(visible=False)
                elif key == 'FOLDER':
                    if (values[key] == ''):
                        valid = False
                        window["-FOLDER-ERR-"].update(visible=True)
                    else:
                        window["-FOLDER-ERR-"].update(visible=False)
                        
                elif key == "-MAXONE-":
                    # if values['-CONFIG-'] != None:
                    if values[key]:
                        if (read_config(values['-CONFIG-'], False)):
                            window['-CONFIG-ERR-'].update(visible=False)
                        else:
                            valid = False
                            window['-CONFIG-ERR-'].update(visible=True)
                elif key == "-MAXTWO-":
                    if values[key]:
                        if wells == None:
                            valid = False
                            window['-WELLS-ERR-'].update(visible=True)
                        else:
                            window['-WELLS-ERR-'].update(visible=False)
                elif key == '-SCRIPT-':
                    if values[key]:
                        window['-SCRIPT-ERR-'].update(visible=False)
                    else:
                        valid = False
                        window['-SCRIPT-ERR-'].update(visible=True)

                if valid:
                    experiment = values
                    configs = {}
                    if wells != None and values['-MAXTWO-']:
                        wells_list = []
                        for i in range(6):
                            if (wells[str(i)]):
                                wells_list.append(i)
                        experiment['WELLS'] = wells_list
                        for well in wells_list:
                            val, electrode_nums, electrode_coords = read_config(wells[f'-CONFIG-{well}-'], False)
                            config = {}
                            config['PATH'] = wells[f'-CONFIG-{well}-']
                            config['E_NUMS'] = electrode_nums
                            config['E_COORDS'] = electrode_coords
                            configs[str(well)] = config
                    else:
                        val, electrode_nums, electrode_coords = read_config(experiment['-CONFIG-'], False)
                        config = {}
                        config['PATH'] = experiment['-CONFIG-']
                        config['E_NUMS'] = electrode_nums
                        config['E_COORDS'] = electrode_coords
                        configs['0'] = config
                        experiment['WELLS'] = [0]
                    
                    experiment['CONFIGS'] = configs
                    save_file(experiment, True)
                    window.close()
                    return f"{experiment['FOLDER']}/{experiment['NAME']}.json"
    
    return None

def start_gui():
    sg.theme('DarkGrey1') 
    layout = [ 
        # [sg.Text('NAME OF TRIAL:'), sg.InputText(key='TRIAL_NAME')], 
        [sg.Button('start-maxlab'), sg.Button('Other'),
        sg.Button('Cancel')]
    ]
    window = sg.Window('Start', layout, finalize=True, resizable=True)

    while True:
        event, values = window.read()
        if (event == 'Cancel' or event == sg.WIN_CLOSED):
            window.close()
            break
        elif event == 'start-maxlab':
            window.close()
            exp = make_experiment()
            if exp == None:
                start_gui()
            else:
                return exp
        elif event == 'Other':
            window.close()
            setup = get_config()
            print(setup)
            if setup == None:
                start_gui()
            else:
                return setup
    
    return None


def make_experiment():
### START WINDOW: 
    
    layout = [ 
                # [sg.Text('NAME OF TRIAL:'), sg.InputText(key='TRIAL_NAME')], 
                [sg.Button('Choose Experiment'), sg.Button('Define Experiment'),
                sg.Button('Cancel')]]
    window = sg.Window('Experiment', layout)

    exp_chosen = False
    experiment = None
    while True:
        event, values = window.read()
        # Check chip ID
        
        # Let user choose to define or choose a preset experiment
        if (event == 'Cancel' or event == sg.WIN_CLOSED):
            experiment = None
            break
        elif event == 'Define Experiment':
            window.close()
            experiment = define_exp(None)
            if not experiment:
                return make_experiment()
            else:
                break
        elif event == 'Choose Experiment':
            window.close()
            experiment = choose_exp(True)
            if not experiment:
                return make_experiment()
            else:
                break

    # valid_exp['FOLDER_NAME'] =
    window.close()
    return experiment



# start the gui if GUI.py is executed as a script
if __name__ == '__main__':
    start_gui()