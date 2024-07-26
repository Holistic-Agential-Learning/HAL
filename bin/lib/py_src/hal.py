import os
import datetime
import shutil
from typing import List
import maxlab as mx

import maxlab as mx
from typing import List


def make_trial_folders(experiment_parameters):
    """ Creates folders for saving data based on a dict, generated from an 
    experiment ``json`` file (see: :ref:`getting-started:Folder Structure`)

    :param experiment_parameters: Holds the experiment paremeters; the following elements are **required**:
            ``'FOLDER'``, ``'NAME'``, ``'WELLS'``
    :type experiment_parameters: ``HAL.json.dict{}``
    :return: Returns the full path of the *trial folder*
    :rtype: ``string``
    """
    today = datetime.datetime.now()

    today_str = today.strftime("%y%m%d")

    home_folder = experiment_parameters['FOLDER']

    json_path = f"{home_folder}/{experiment_parameters['NAME']}.json"

    full_folder_path = f"{home_folder}/{today_str}"
    print(f"full_folder_path: {full_folder_path}")

    if not os.path.exists(full_folder_path):
        os.makedirs(full_folder_path)
    
    # create the trial folder
    trial = 0
    trial_path = ""
    while True:
        trial_path = f"{full_folder_path}/{trial}"

        if not os.path.exists(trial_path):
            os.makedirs(trial_path)
            break
            
        trial += 1
    
    print(f"Trial path: {trial_path}")
    
    wells = experiment_parameters['WELLS']

    # create well folders
    for well in wells:
        well_path = f"{trial_path}/well{well}"

        print(f"Making well folder: {well_path}")

        os.makedirs(well_path)

        json_copy = f"{well_path}/arguments.json"
        print(f"Creating {json_copy}")

        # shutil.copyfile(json_path, json_copy)

    return trial_path

def make_trial_folders_raw(parent_path, experiment_name, chip_id, wells):
    """ Creates folders for saving data without using a dict, in the HAL 
    specified folder format (see :ref:`getting-started:Folder Structure`).

    :param parent_path: full path of the parent folder
    :type parent_path: ``string``

    :param experiment_name: name of experiment
    :type experiment_name: ``string``

    :param chip_id: chip id
    :type chip_id: ``int``

    :param wells: list of wells that the experiment will run on 
    :type wells: ``List[int]``

    :return: Returns the full path of the *trial folder*
    :rtype: ``string``
    """
    today = datetime.datetime.now()

    today_str = today.strftime("%y%m%d")

    full_folder_path = f"{parent_path}/{experiment_name}/{chip_id}/{today_str}"
    # print(f"full_folder_path: {full_folder_path}")

    if not os.path.exists(full_folder_path):
        os.makedirs(full_folder_path)
    
    # create the trial folder
    trial = 0
    trial_path = ""
    while True:
        trial_path = f"{full_folder_path}/{trial}"

        if not os.path.exists(trial_path):
            os.makedirs(trial_path)
            break
            
        trial += 1
    
    # print(f"Trial path: {trial_path}")
    
    # create well folders
    for well in wells:
        well_path = f"{trial_path}/well{well}"

        # print(f"Making well folder: {well_path}")

        os.makedirs(well_path)

    return trial_path

#TODO: move this to an Array class.
def connect_stim_units_to_stim_electrodes(stim_electrodes: List[int], array: mx.Array) -> List[int]:
    """Connects stimulation units to stimulation electrodes. This function 
    was taken from example code from MaxWell.

    :param stim_electrodes: list of stimulation electrodes to connect
    :type stim_electrodes: ``List[int]``
    :param array: MaxWell array generated from a list of recording/stimulation electrodes
    :type array: ``mx.Array``
    :raises RuntimeError: when a stimulation channel cannot connect to a stimulation electrode
    :raises RuntimeError: when two electrodes are connected to the same unit
    :return: a list of stimulation units
    :rtype: ``List[int]``
    """
    stim_units: List[int] = []
    for stim_el in stim_electrodes:
        array.connect_electrode_to_stimulation(stim_el)
        stim = array.query_stimulation_at_electrode(stim_el)
        if len(stim) == 0:
            raise RuntimeError(
                f"No stimulation channel can connect to electrode: {str(stim_el)}"
            )
        stim_unit_int = int(stim)
        if stim_unit_int in stim_units:
            raise RuntimeError(
                f"Two electrodes connected to the same stim unit. This is not allowed. Please Select a neighboring electrode of {stim_el}!"
            )
        else:
            stim_units.append(stim_unit_int)
    return stim_units