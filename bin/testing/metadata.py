'''
Testing new metadata structure.
Author: caitlin
'''

import os, sys
import time
import re

def format_metadata(metadata: dict):
    """
    Formats. 

    :param metadata: Experiment metadata 
    :type metadata: dict
    """     

    # Format checks
    if not re.fullmatch(r"\d{6}", str(metadata['Plate date'])):
        raise ValueError("Plate date must be in the format YYMMDD.")
    metadata['Plate date'] = int(metadata['Plate date'])
    
    if not re.fullmatch(r"\d+", str(metadata['DIV'])):
        raise ValueError("DIV must be an integer.")
    metadata['DIV'] = int(metadata['DIV'])
    
    if not isinstance(metadata["Well IDs"], list):
        raise ValueError("Well IDs must be a list of integers.")
    if not all(isinstance(i,int) for i in metadata["Well IDs"]):
        raise ValueError("Well IDs must be a list of integers.")
    
    if not isinstance(metadata["Conditions"], list) or (len(metadata["Well IDs"]) != len(metadata["Conditions"]) and len(metadata["Conditions"])!=0):
        raise ValueError("Conditions must be a list the same length as the number of wells or length 0.")
    
    # Convert the experiment ID to camelCase so there's no underscores or spaces
    # e.g. "wave training" or "wave_training" --> "waveTraining"
    parts = re.split(r'[_\s]+', metadata["Exp ID"].strip())
    if parts:
        if len(parts)>1:
            metadata["Exp ID"] = parts[0].lower() + ''.join(word.capitalize() for word in parts[1:]) # replace experiment ID in the metadata dict
        else:
            metadata["Exp ID"] = parts[0][0].lower()+parts[0][1:] # make sure it starts lowercase
    else:
        raise ValueError("Enter an valid string Experiment ID.")
    
    return metadata


metadata = {'Plate date': 250913,
            'DIV':14,
            'Chip ID':'M07654',
            'Exp ID': 'network scan', # the task 
            'Well IDs':[1,2], 
            'Conditions':[]} # conditions decoded based on the particular task

metadata = format_metadata(metadata)

print(metadata)
