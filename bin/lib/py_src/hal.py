import os
import datetime


def make_trial_folders(experiment_parameters):
    today = datetime.datetime.now()

    today_str = today.strftime("%y%m%d")

    full_folder_path = f"{experiment_parameters['FOLDER']}/{today_str}"
    print(f"full_folder_path: {full_folder_path}")

    if not os.path.exists(full_folder_path):
        os.mkdir(full_folder_path)
    
    # create the trial folder
    trial = 0
    trial_path = ""
    while True:
        trial_path = f"{full_folder_path}/{trial}"

        if not os.path.exists(trial_path):
            os.mkdir(trial_path)
            break
            
        trial += 1
    
    print(f"Trial path: {trial_path}")
    
    wells = experiment_parameters['WELLS']

    for well in wells:
        well_path = f"{trial_path}/well{well}"

        print(f"Making well folder: {well_path}")

        os.mkdir(well_path)


    return trial_path