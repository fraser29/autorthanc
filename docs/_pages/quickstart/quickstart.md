---
layout: default
title: Quick Start
---

# Quick Start

- Clone or download this repository. 
- Copy env_example to .env
- Edit .env, customise the variables for your specific setup:
  - ORTHANC_AUTOMATION_JSON_SCRIPTS_PATH
  - ORTHANC_AUTOMATION_STORAGE_PATH
- Make the "Automation" directories (otherwise docker will make for you and they will be owned by root)
- Add *.json files to your ORTHANC_AUTOMATION_JSON_SCRIPTS_PATH 
  - Copy and edit the template file "automation_template.json" found in orthanc/automation_scripts 
- Start the container: 
```bash
docker compose up --build -d
```
- View the running ORTHANC instance at [localhost/orthanc](http://localhost/orthanc)
- Add some dicoms to your ORTHANC instance and watch the automation take place