# AUTORTHANC

A docker container based off **NGINX + Orthanc + Postgres** including python based automation for downloading studies based on prescribed rules. 

## Base Docker

Docker based infrastructure for Orthanc (with postgres). 

## Quick Start

Copy env_example to .env

Edit .env, specifically variables:
- ORTHANC_DB_MNT : The location (on local machine) for data (dicom) storage
- ORTHANC_AUTO_SCRIPTS : The location (on local machine) where autorthanc will find your .json files defining rules for how to process new studies. 
- ORTHANC_AUTOMATION_DATA_STORAGE : The location where data identified by .json scripts found in *ORTHANC_AUTO_SCRIPTS* will be downloaded to. 
- POSTGRES_PASSWORD : the postgres DB password. 

Optional variables to edit: 
- GROUPID (and USERID) : The IDs that should be used to give ownership to the automatically identified and downloaded datasets. *If you are on a single user linux machine, these will likely remain as 1000 & 1000*

## 

*nginx.conf* line 6 : substitute your local machines IP address



=======

## DEVELOPMENT 

Idea is that have standard osimis orthanc docker, with a mounted volume at /var/lib/automation

A python script runs upon every study stable shall read all json files under /var/lib/automation/*.json 

Each file contains instructions: 
1. To to define if the inspected study belongs to this rule
2. Actions to take if study passes (1)

An automation_template.json file exists in directory 'automation_scripts'. 

### automation.json file

- The automation_template.json will be ignored by the Automation.py script. 
- Copy the automation_template.json to build your own automation rule.
- **Name** your new automation.json to something sensible and unique in the "automation_scripts" directory.
- Studies that pass your automation.json rule will be downloaded to a directroy named the same as your automation.json script under *AUTOMATION_DATA_STORAGE* (see env_example) 

### Example:

If your *AUTOMATION_DATA_STORAGE* variable is set to "/home/username/data" and you supply an automation json named: brain_study_X.json. 
When that automation script identifies a new study arriving in the dicom server, say based on the following rules:
- StudyDescription tag contains "brain"
- (for any series in study) SeriesDescription tag contains "axial t1"

Then that study will be automatically downloaded to directory:
```bash
/home/username/data/brain_study_x/PatientID-PatientName
```

The template file is as follows and below are explanations on tags:

```json
{
    "CheckOn": "Study", 
    "IsActive": true, 
    "OverwriteIfAlreadyDownloaded": true, 
    "Comment": "CHANGEME: enter something sensible and your initials", 
    "Tags": [
        {
            "TagName": "PatientName",
            "Level": "Patient",
            "Value": "CHANGEME_or_delete_block"
        },
        {
            "TagName": "StudyDescription",
            "Level": "Study",
            "Value": "CHANGEME_or_delete_block"
        },
        {
            "TagName": "SeriesDescription",
            "Level": "Series",
            "Value": "CHANGEME_or_delete_block"
        }
    ]
}
```

### automation json tags: 

- CheckOn:
  - str : "Study" or "Series" : Do we check this rule when a Study is stable or a Series is stable
- IsActive:
  - bool : Can set inactive. 
- OverwriteIfAlreadyDownloaded
  - bool : Usually leave as true, incase a study is incompletely pushed and receives more data at a later time. 
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

*NOTE* : package [miresearch](https://github.com/fraser29/miresearch) is designed to work in combination with autorthanc by watching docnload directorys for completed data sets to then perform extra post processing steps, e.g. to initiate processing pipelines. 



--------------------

Docker images :
- osimis/orthanc:20.2.0
- postgres:12.1

To deploy the infrastructure, run `docker compose up` or `docker compose up -d` (background task).

## Access OHIF Viewer
A few seconds after deploying the images, the viewer can be accessed at [http://127.0.0.1:81/](http://127.0.0.1:81/) from your browser.

## Access Orthanc admin interface

Orthanc's admin interface can be reached from the navigator at [http://127.0.0.1:81/pacs-admin](http://127.0.0.1:80/pacs-admin), then sign in

- Username: **my_username**
- Password: **my_password**

## How to shutdown and clean up

```
# interrupt containers
docker compose stop 

# remove containers
docker compose rm -f

# remove virtual volumes and networks interfaces
docker volume prune -f
docker network prune -f

# remove local persisting data of the volumes
rm -rf orthanc_db pg_data
```

## Python script action:

- Triggered on StudyStable (and SeriesStable possible - but not used) 
- Recognises a series / study based upon rules defined in json script 
- Performs actions 
  - First to DOWNLOADING directory
  - Once complete copies to QUEUED directory
