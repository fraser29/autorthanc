---
layout: default
title: Tutorial
---


### Example:

If you copy env_example to .env and set *ORTHANC_AUTOMATION_STORAGE_PATH* to */home/username/data*

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
    "Action" : "DOWNLOAD",
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
    "Action" : "DOWNLOAD or FORWARD",
    "DestinationModality": "Name of destination for FORWARD",
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
