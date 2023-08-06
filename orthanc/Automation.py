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

# TODO move to config
SERIES_CONTAINS_STR = ''
outputDir = '/output'
DOWNLOADING = 'DOWNLOADING'
QUEUED = 'QUEUED'
USERNAME = 1000
GROUPNAME = 1000



def writeDictionaryToJSON(fileName, dictToWrite):
    with open(fileName, 'w') as fp:
        json.dump(dictToWrite, fp, indent=4, sort_keys=True)
    return fileName


def parseJsonToDictionary(fileName):
    with open(fileName, 'r') as fid:
        myDict = json.load(fid)
    return myDict

def readMasterJSON(masterFile):
    masterD = parseJsonToDictionary(masterFile)
    


def initStorage():
    os.makedirs(f'{outputDir}/{DOWNLOADING}', exist_ok=True)
    os.makedirs(f'{outputDir}/{QUEUED}', exist_ok=True)

def getInstances(seriesID):
    allInstanceIds = json.loads(orthanc.RestApiGet(f"/series/{seriesID}/instances"))
    return allInstanceIds

def writeOutSeriesIDToFile(seriesID): # For testing
    with open(f'{outputDir}/uro_out.txt', 'w') as fid:
        fid.write(seriesID)

def getOutputDir(seriesID, DOWNLOAD=False):
    metadata = json.loads(orthanc.RestApiGet(f'/series/{seriesID}'))
    metaPat = json.loads(orthanc.RestApiGet(f'/studies/{metadata["ParentStudy"]}'))
    prefix = f'{DOWNLOADING}/' if DOWNLOAD else f'{QUEUED}/'
    name = metaPat["PatientMainDicomTags"]["PatientName"].split('^')[0]
    patientDir = f'{outputDir}/{prefix}{metaPat["PatientMainDicomTags"]["PatientID"]}-{name}'
    seriesOutDir = f'{patientDir}-SE{metadata["MainDicomTags"]["SeriesNumber"]}-{metadata["MainDicomTags"]["SeriesDate"]}-{metadata["MainDicomTags"]["SeriesInstanceUID"]}'
    return seriesOutDir

def changeOwnership(directory, userName, groupName):
    os.system(f"chown -R {userName}:{groupName} {directory}")

def writeOutSeriesToDirectory(seriesID, FORCE=False):
    queuedDIR = getOutputDir(seriesID, DOWNLOAD=False) # QUEUED
    if os.path.isdir(queuedDIR):
        if FORCE:
            shutil.rmtree(queuedDIR)
        else:
            return queuedDIR
    instances = getInstances(seriesID)
    downloadDIR = getOutputDir(seriesID, DOWNLOAD=True) # DOWNLOADING
    os.makedirs(downloadDIR, exist_ok=True)
    for instanceId in instances:
        dicom = instanceToPyDicom(instanceId['ID'])
        dicom.save_as(f'{downloadDIR}/{dicom.SOPInstanceUID}.dcm', write_like_original=True)
    os.rename(downloadDIR, queuedDIR)
    changeOwnership(queuedDIR, USERNAME, GROUPNAME)
    return queuedDIR

def confirmSeriesWrittenOut(seriesID, destinationDir):
    metadata = json.loads(orthanc.RestApiGet(f'/series/{seriesID}'))
    nInstances = len(metadata['Instances'])
    print(f'DEBUG: Expect {nInstances} instances -> list dir count = {len(os.listdir(destinationDir))}')
    return len(os.listdir(destinationDir)) == nInstances

def instanceToPyDicom(instanceID):
    f = orthanc.GetDicomForInstance(instanceID)
    # Parse it using pydicom
    dicom = pydicom.dcmread(io.BytesIO(f))
    return dicom

def isSeriesDescription(seriesID, matchStr):
    metadata = json.loads(orthanc.RestApiGet(f'/series/{seriesID}'))
    try:
        seriesDescription = metadata["MainDicomTags"]["SeriesDescription"]
    except KeyError:
        return False
    return matchStr.lower() in seriesDescription.lower()

def isUrography(seriesID):
    metadata = json.loads(orthanc.RestApiGet(f'/series/{seriesID}'))
    try:
        seriesDescription = metadata["MainDicomTags"]["SeriesDescription"]
        seriesNumber = int(metadata["MainDicomTags"]["SeriesNumber"])
    except KeyError:
        return False
    return seriesDescription.endswith("(time)") and (seriesNumber < 100)

def isUrographyPDF(seriesID):
    metadata = json.loads(orthanc.RestApiGet(f'/series/{seriesID}'))
    try:
        seriesDescription = metadata["MainDicomTags"]["SeriesDescription"]
        seriesNumber = int(metadata["MainDicomTags"]["SeriesNumber"])
    except KeyError:
        return False
    return seriesDescription.endswith("ResultsPDF")

# ================================================================================================================
def AutoPipelineOnStableSeries(seriesID, FORCE=False):
    # TODO read master.json and get all ID  and action stuff
    # tf = isSeriesDescription(seriesID, SERIES_CONTAINS_STR)
    tf = isUrography(seriesID)
    if tf:
        print(f'Have new series {seriesID}. Is UROGRAPHY: {tf}')
        outputDir = writeOutSeriesToDirectory(seriesID, FORCE)
        if confirmSeriesWrittenOut(seriesID, outputDir): # Checks file count vs count in Orthanc
            orthanc.RestApiDelete(f'/series/{seriesID}')
            return 0
        else:
            # In this case - hopefully get some more dicoms and then force the IS_STABLE flag again
            # Or at least not delete and can manually write (in case there was a writting problem)
            return 1
    tf2 = isUrographyPDF(seriesID)
    if tf2:
        print(f'Have new series {seriesID}. Is UROGRAPHYPDF: {tf2}')
        orthanc.RestApiPost('/modalities/PACS/store', seriesID)
        # orthanc.RestApiDelete(f'/series/{seriesID}')
        # return 0
    return 10 # if is not URO - still success
            
# ================================================================================================================


def ManualCallURO(output, uri, **request):
    if request['method'] == 'GET':
        # Retrieve the series ID from the regular expression (*)
        seriesId = request['groups'][0]
        result = AutoPipelineOnStableSeries(seriesId, FORCE=True)
        if result == 0:
            output.AnswerBuffer("SUCCESS: Pipeline initiated - you may close this page", 'text/plain')
        elif result == 10:
            output.AnswerBuffer("This series was not identified as a Urography series. If you are sure it is, please contact Fraser with examID and series number.", 'text/plain')
        else:
            output.AnswerBuffer("Oh no! Error encountered: please contact Fraser (fraser.callaghan@kispi.uzh.ch OR 3130)", 'text/plain')
    else:
        output.SendMethodNotAllowed('GET')

def OnChange(changeType, level, resource):

    # at startup, we should detect all series that are currently in
    # Orthanc and we shall queue them "for processing"
    if changeType == orthanc.ChangeType.ORTHANC_STARTED:
        allSeriesIds = json.loads(orthanc.RestApiGet("/series"))
        for seriesId in allSeriesIds:
            AutoPipelineOnStableSeries(seriesId, FORCE=False)

    elif changeType == orthanc.ChangeType.ORTHANC_STOPPED:
        pass

    # everytime a new series is received, we shall check it then process
    elif changeType == orthanc.ChangeType.STABLE_SERIES:
        AutoPipelineOnStableSeries(resource, FORCE=True)
        # Force true so that if paused and then restarted then will overwrite


# ================================================================================================================
#   MAIN
# ================================================================================================================
# add two restful callbacks

# (1) Add button on series labelled "Send series to Urography pipeline"
#        This button calls href: '/uropipeline/' + seriesID
#        This href is linked back to function here: ManualCallURO
orthanc.RegisterRestCallback('/uropipeline/(.*)', ManualCallURO)  # (*)
# here add the actual button
with open("/python/extend-explorer.js", "r") as f:
    orthanc.ExtendOrthancExplorer(f.read())

# (2) Register a callback to the OnChange signal
#       When ever a change occurs then "OnChange" function called
#       If the change is what we want (a stable series) then check if is URO and kick off pipeline
orthanc.RegisterOnChangeCallback(OnChange)

# This is ensure set up correctly
initStorage()
