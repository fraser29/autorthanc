# AUTORTHANC

A docker container based off **NGINX + Orthanc + Postgres** including python based automation for downloading studies based on prescribed rules. 

## Base Docker

Docker based infrastructure for Orthanc (with postgres). 

## Quick Start

- Copy env_example to .env
- Edit .env, customise the variables for your specific setup:
- Make the "Automation" directories (otherwise docker will make for you and they will be owned by root)
- Add *.json files to your ORTHANC_AUTOMATION_JSON_SCRIPTS_PATH 
- Start the container: 
```bash
docker compose up --build -d
```
- View the running ORTHANC instance at [localhost/orthanc](http://localhost/orthanc)
- Add some dicoms to your ORTHANC instance and watch the automation take place

----- 


## AUTOMATION

The automation portion of this docker will inspect every new study passed to the Orthanc instance, once that study has become "stable" 

Stable is defined as no new images appeared for a period of ?? seconds. 

If that study meets criterior defined by an XXX.json under ORTHANC_AUTOMATION_JSON_SCRIPTS_PATH then that study will be downloaded to a patient specific directory under: *ORTHANC_AUTOMATION_STORAGE_PATH/XXX/pid_name_examid*

**Note:** During the downloading the output directory will be named, e.g.: 
*ORTHANC_AUTOMATION_STORAGE_PATH/XXX/pid_name_examid.WORKING*

Once downloading is finished the name will be changed to:
*ORTHANC_AUTOMATION_STORAGE_PATH/XXX/pid_name_examid*

Of course *pid*, *name* and *examid* are replaced with study specific values.  

### automation.json file

**NOTE** Any *.json files with *master* or *template* in their name will be ignoree by the automation script. 

- The automation_template.json will be ignored by the atomation.py script. 
- Copy the automation_template.json to build your own automation rule.
- **Name** your new automation.json to something sensible and unique in the "automation_scripts" directory.
- Studies that pass your automation.json rule will be downloaded to a directroy named the same as your automation.json script under *AUTOMATION_DATA_STORAGE*


### Example:

You copy env_example to .env and set *ORTHANC_AUTOMATION_STORAGE_PATH* to */home/username/data*
If you save in *ORTHANC_AUTOMATION_JSON_SCRIPTS_PATH* an automation json named: brain_study_X.json. 
When that automation script identifies a new study arriving in the dicom server, say based on the following rules:
- StudyDescription tag contains "brain"
- (for any series in study) SeriesDescription tag contains "axial t1"

Then that study will be automatically downloaded to directory:
```bash
/home/username/data/brain_study_x/PatientID-PatientName
```

In this case the brain_study_x.json would look something like:
```json
{
    "CheckOn": "Study", 
    "IsActive": true, 
    "OverwriteIfAlreadyDownloaded": true, 
    "Comment": "Find subjects for brain study", 
    "Tags": [
        {
            "TagName": "StudyDescription",
            "Level": "Study",
            "Value": "brain"
        },
        {
            "TagName": "SeriesDescription",
            "Level": "Series",
            "Value": "axial t1"
        }
    ]
}
```


### Templates

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

*NOTE* : package [miresearch](https://github.com/fraser29/miresearch) is designed to work in combination with autorthanc by watching download directorys for completed data sets to then perform extra post processing steps, e.g. to initiate processing pipelines. 



--------------------

Docker images :
- orthancteam/orthanc:20.2.0
- postgres:12.1

To deploy the infrastructure, run `docker compose up` or `docker compose up -d` (background task).


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

