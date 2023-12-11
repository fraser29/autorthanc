# NGINX + Orthanc + Postgres

Docker based infrastructure for OHIF Viewer, Orthanc (with postgres)
=======

## DEVELOPMENT 

Idea is that have standard osimis orthanc docker, with a mounted volume at /var/lib/automation

Add a python script that on every study stable - read /var/lib/automation/master.json 

 - Get list of study_stable instructions
 - if study_stable_instruction_XXX.json is present then check if meets conditions. If so then run. 
   - possible to repeat on series_stable (but suggest not to do this). 

Also in master.json have option to run do all instructions check daily at hour XX (every hour run to check this).

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
