---
layout: default
title: Usage
---

# Usage

autorthanc may be entirely customised via the .env file in the root directory. 

## .env file

Variables defined in the .env file are used to customise the setup. 

Detailed description of the variables set in .env and their defaults follow: 

```.env
# The user and group ID to set for all data once written out. 
## The container runs with user root and thus to avoid permission error with data written to the host volume the following IDs are used to set permissions upon completion of writting.
UID=1000
GID=1000

# The port on which to expose the ORTHANC web interface:
ORTHANC_WEB_PORT=80

# The path on the HOST machine where the storage of dicom files will be:
ORTAHNC_DB_STORAGE_PATH=/path/to/local/directory/for/dicom/storage
# The time (in seconds) after which if no changes have been made, then autorthanc will declare a study stable: 
ORTHANC_STABLE_AGE=300

# The AET name and port used for the dicom node that autorthanc exposes:
ORTHANC_AET_NAME=AUTORTHANCAET
ORTHANC_AET_PORT=4006

# The dicom modalities that autorthanc is associated with:
## Note this needs to be a single line:
ORTHANC_DICOM_MODALITIES={"MODALITY_NAME": ["REMOTEAETNAME", "REMOTE-IP", 4242]}

# The paths on the HOST machine where JSON automation scripts should reside (these may be added to and modified while autorthanc is running). And where downloaded data will be saved - data identified by XYZ.json will be saved under a directory at ORTHANC_AUTOMATION_STORAGE_PATH/XYZ 
## These directroies should exist with desired (user) ownership on the local system
ORTHANC_AUTOMATION_JSON_SCRIPTS_PATH=/path/to/local/directory/for/json/scripts
ORTHANC_AUTOMATION_STORAGE_PATH=/path/to/local/storage/for/download/data

```
  
# Automation

The automation portion of this docker will inspect every new study passed to the Orthanc instance, once that study has become "stable". 

Stable is defined as no new images appeared for a period of X seconds (X is defined using variable ORTHANC_STABLE_AGE in the .env file - defaults to 300 seconds). 

If that study meets criteria defined by an XXX.json under ORTHANC_AUTOMATION_JSON_SCRIPTS_PATH then that study will be downloaded to a patient specific directory under: *ORTHANC_AUTOMATION_STORAGE_PATH/XXX/pid-name-examid*

**Note:** During the downloading the output directory will be named, e.g.: 
*ORTHANC_AUTOMATION_STORAGE_PATH/XXX/pid-name-examid.WORKING*

Once downloading is finished the name will be changed to:
*ORTHANC_AUTOMATION_STORAGE_PATH/XXX/pid-name-examid*

Of course *pid*, *name* and *examid* are replaced with study specific values.  

### automation.json file

**NOTE** Any *.json files with *master* or *template* in their name will be ignored by the automation script. 

- The automation_template.json will be ignored by the automation.py script. 
- Copy the automation_template.json to build your own automation rule.
- **Name** your new automation.json to something sensible and unique in the "automation_scripts" directory.
- Studies that pass your automation.json rule will be downloaded to a directory named the same as your automation.json script under *AUTOMATION_DATA_STORAGE*

## automation control

The automation is defined via JSON files in the location ORTHANC_AUTOMATION_JSON_SCRIPTS_PATH set by the .env file. 

These files may be added at any time (a restart of the docker container is not necessary). 



### automation json tags: 

- CheckOn:
  - str : "Study" or "Series" : Do we check this rule when a Study is stable or a Series is stable
- IsActive:
  - bool : Can set inactive. 
- Comment: 
  - str : A comment about the rule
- Tags:
  - list of objects : Tags defining the decision making of if a study / series passes this rule check

  - TagName: 
    - str: the name of the dicom tag to check
  - Level:
    - TO REMOVE
  - Value:
    - str : The value that the dicom tag TagName **MUST** include for the rule to pass. 

**NOTE** 
- Multiple TagName / Value pair objects may be included under Tags.  
- **EVERY** Tag object must pass for the entire automation.json to pass. 


.env file defines local directory for automation jsons. This local directory is mounted at /automation in the docker container.

A study_stable or series_stable task may do any/all of the  following steps:
- Download study / series
- Anonymise  dicoms
- ZIP data. 

*NOTE* : package [miresearch](https://github.com/fraser29/miresearch) is designed to work in combination with autorthanc by watching download directories for completed data sets to then perform extra post processing steps, e.g. to initiate processing pipelines. 


