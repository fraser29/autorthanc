
# Example outputs from RestAPI calls (taken from docs)

# STUDY

Note - also some patient info here

```json
// $ curl https://orthanc.uclouvain.be/demo/tools/find -d '{"Level":"Study","Query":{"PatientName":"KNIX"},"Expand":true}'
[
  {
    "ID" : "b9c08539-26f93bde-c81ab0d7-bffaf2cb-a4d0bdd0",
    "IsStable" : true,
    "LastUpdate" : "20180414T091528",
    "MainDicomTags" : {
       "InstitutionName" : "0ECJ52puWpVIjTuhnBA0um",
       "ReferringPhysicianName" : "1",
       "StudyDate" : "20070101",
       "StudyDescription" : "Knee (R)",
       "StudyID" : "1",
       "StudyInstanceUID" : "1.2.840.113619.2.176.2025.1499492.7391.1171285944.390",
       "StudyTime" : "120000.000000"
    },
    "ParentPatient" : "6816cb19-844d5aee-85245eba-28e841e6-2414fae2",
    "PatientMainDicomTags" : {
       "PatientID" : "ozp00SjY2xG",
       "PatientName" : "KNIX"
    },
    "Series" : [
       "20b9d0c2-97d85e07-f4dbf4d2-f09e7e6a-0c19062e",
       "edbfa0a9-fa2641d7-29514b1c-45881d0b-46c374bd",
       "f2635388-f01d497a-15f7c06b-ad7dba06-c4c599fe",
       "4d04593b-953ced51-87e93f11-ae4cf03c-25defdcd",
       "5e343c3e-3633c396-03aefde8-ba0e08c7-9c8208d3",
       "8ea120d7-5057d919-837dfbcc-ccd04e0f-7f3a94aa"
    ],
    "Type" : "Study"
  }
]
```

# SERIES

```json
{
  "ExpectedNumberOfInstances" : 45,
  "ID" : "2cc6336f-2d4ae733-537b3ca3-e98184b1-ba494b35",
  "Instances" : [
     "41bc3f74-360f9d10-6ae9ffa4-01ea2045-cbd457dd",
     "1d3de868-6c4f0494-709fd140-7ccc4c94-a6daa3a8",
     <...>
     "1010f80b-161b71c0-897ec01b-c85cd206-e669a3ea",
     "e668dcbf-8829a100-c0bd203b-41e404d9-c533f3d4"
  ],
  "MainDicomTags" : {
     "Manufacturer" : "Philips Medical Systems",
     "Modality" : "PT",
     "NumberOfSlices" : "45",
     "ProtocolName" : "CHU/Body_PET/CT___50",
     "SeriesDate" : "20120716",
     "SeriesDescription" : "[WB_CTAC] Body",
     "SeriesInstanceUID" : "1.3.46.670589.28.2.12.30.26407.37145.2.2516.0.1342458737",
     "SeriesNumber" : "587370",
     "SeriesTime" : "171121",
     "StationName" : "r054-svr"
  },
  "ParentStudy" : "9ad2b0da-a406c43c-6e0df76d-1204b86f-78d12c15",
  "Status" : "Complete",
  "Type" : "Series"
}
```
