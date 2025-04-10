# AUTORTHANC

A docker container based off **NGINX + Orthanc + Postgres** including python based automation for downloading studies based on prescribed rules. 

## Base Docker

Docker based infrastructure for Orthanc (with postgres). 

## Quick Start

- Copy env_example to .env
- Edit .env, customise the variables for your specific setup:
- Make the "Automation" directories (otherwise docker will make for you and they will be owned by root)
- Start the container: 
```bash
docker compose up --build -d
```
- View the running ORTHANC instance at [localhost/orthanc](http://localhost/orthanc)
- Add *.json files to your ORTHANC_AUTOMATION_JSON_SCRIPTS_PATH 
- Add some dicoms to your ORTHANC instance and watch the automation take place

----- 


## AUTOMATION

The automation portion of this docker will inspect every new series and study passed to the Orthanc instance, once that sereis/study has become "stable". 

Stable is defined as no new images appeared for a period of X seconds (X is defined using variable ORTHANC_STABLE_AGE in the .env file - defaults to 60 seconds). 

If that study meets criterior defined by an XXX.json under ORTHANC_AUTOMATION_JSON_SCRIPTS_PATH then that study will be downloaded to a patient specific directory under: *ORTHANC_AUTOMATION_STORAGE_PATH/XXX/pid-name-examid*

**Note:** During the downloading the output directory will be named, e.g.: 
*ORTHANC_AUTOMATION_STORAGE_PATH/XXX/pid-name-examid.WORKING*

Once downloading is finished the name will be changed to:
*ORTHANC_AUTOMATION_STORAGE_PATH/XXX/pid-name-examid*

Of course *pid*, *name* and *examid* are replaced with study specific values.  

### automation.json file

**NOTE** Any *.json files with *master* or *template* in their name will be ignored by the automation script. 

- Copy the automation_template.json to build your own automation rule.
- **Name** your new automation.json to something sensible and unique in the "automation_scripts" directory.
- Studies that pass your automation.json rule will be downloaded to a directroy named the same as your automation.json script under *AUTOMATION_DATA_STORAGE*

### Post processing

Often, the reason for exporting a dataset using AUTORTHANC is to carry out some post-processing. 

Please see the python package [hurahura](https://fraser29.github.io/hurahura/) for this. 

Alternatively, a script named "*directory_watch.sh*" is included with this repository. 

### Clean up

Clean up is left to the user. Please see [OrthancManager](https://github.com/fraser29/OrthancManager) for a user friendly toolkit that can interact with the Orthanc API from the commandline. 

--------------------

## Docker images :
- orthanc
- postgres:16

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

See the full documentation [here](https://fraser29.github.io/autorthanc/)

# Use the OHIF viewer

An override file is provided to use this Orthanc implementation with the OHIF viewer. This sets some CORS headers to allow the OHIF viewer to work.

```bash
docker compose -f docker-compose.ohif.yml up -d

```

Run the OHIF viewer at [localhost:3000](http://localhost:3000) via: 

```bash
APP_CONFIG=config/local_orthanc.js yarn run start
```


