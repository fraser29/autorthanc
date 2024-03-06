# -*- coding: utf-8 -*-

"""
Automation pipeline

@author: Fraser Callaghan
@date: July 2023
"""

import orthanc
import os
import json
import pydicom
import io
import shutil
import logging

# ============ CONFIG ==============================================================================
auto_scripts_dir="/automation_scripts"
output_dir="/output"
DOWNLOAD_DIR = os.path.join(output_dir, 'DOWNLOADING')
QUEUED_DIR = os.path.join(output_dir, 'QUEUED')
USERID = 1000
GROUPID = 1000
logfile = os.path.join(auto_scripts_dir, 'orthanc_automation.log')

# ============ LOGGING =============================================================================
logger = logging.getLogger(f"autorthanc")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(logfile, encoding='utf-8')
fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-7s | %(name)s | %(message)s', 
                                  datefmt='%d-%b-%y %H:%M:%S'))
logger.addHandler(fh)
logging.info('Autorthanc automation initiated.')


# -------------------------------------------------------------------------------------------------
def initStorage():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(QUEUED_DIR, exist_ok=True)
    logging.info('Autorthanc storage initiated.')
    os.makedirs(QUEUED_DIR+'/COOL', exist_ok=True)

def OnChange(changeType, level, resource):
    if changeType == orthanc.ChangeType.ORTHANC_STARTED:
        pass

    elif changeType == orthanc.ChangeType.ORTHANC_STOPPED:
        pass

    # everytime a new study is received, we shall check it then process
    elif changeType == orthanc.ChangeType.STABLE_STUDY:
        try: 
            print(f"Stable study: {resource}")
            # Force true so that if paused and then restarted then will overwrite
        except Exception as e: # Catch all general exceptions and debug
            logger.critical(e)



# ================================================================================================================
#   MAIN
# ================================================================================================================
# add restful callbacks

# (1) Register a callback to the OnChange signal
#       When ever a change occurs then "OnChange" function called
#       If the change is what we want (a stable series) 
orthanc.RegisterOnChangeCallback(OnChange)

# ================================================================================================================
#   MAIN
# ================================================================================================================

# This is ensure set up correctly
initStorage()
