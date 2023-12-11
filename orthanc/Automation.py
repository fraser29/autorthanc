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
auto_scripts="/auto_scripts"
output="/output"
DOWNLOAD_DIR = os.path.join(output, 'DOWNLOADING')
QUEUED_DIR = os.path.join(output, 'QUEUED')
USERID = 1000
GROUPID = 1000
logfile = os.path.join(auto_scripts, 'orthanc_automation.log')

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

def getAllAutomationDictionary():
    autoscripts = [os.path.join(auto_scripts, i) for i in os.listdir(auto_scripts) if \
                   (i.endswith('json') and (not i.startswith('master')) and (not 'template' in i))]
    autoDicts = []
    for iFile in autoscripts:
        try:
            iDict = parseJsonToDictionary(iFile)
            if iDict.get("IsActive", False):
                iDict['ID'] = os.path.splitext(os.path.split(iFile)[1])[0]
                autoDicts.append(iDict)
        except json.decoder.JSONDecodeError:
            logger.error(f"{iFile} has incorrect format")
        except:
            logger.error(f"Error reading {iFile}")
    return autoDicts

def doesStudyMatchAutoDict(studyID, autoDict):
    metaPatient = json.loads(orthanc.RestApiGet(f'/studies/{studyID}'))
    metaStudy = json.loads(orthanc.RestApiGet(f'/studies/{studyID}'))
    metaSeriesList = [json.loads(orthanc.RestApiGet(f'/series/{iSeries}')) for iSeries in metaStudy['Series']]
    allTF = []
    for iTag in autoDict['Tags']:
        if iTag['Level'].lower() == 'patient':
            thisValue = metaPatient['MainDicomTags'][iTag['TagName']].lower()
            allTF.append(iTag['Value'].lower() in thisValue)
        elif iTag['Level'].lower() == 'study':
            thisValue = metaStudy['MainDicomTags'][iTag['TagName']].lower()
            allTF.append(iTag['Value'].lower() in thisValue)
        elif iTag['Level'].lower() == 'series':
            thisValues = [i['MainDicomTags'][iTag['TagName']] for i in metaSeriesList]
            tf = [iTag['Value'].lower() in i for i in thisValues]
            allTF.append(any(tf))
    return all(allTF)


def checkAutomationScriptsForStudy(studyID):
    allAutoScripts = getAllAutomationDictionary()
    resDicts = []
    for iAuto in allAutoScripts:
        if doesStudyMatchAutoDict(studyID, iAuto):
            resDicts.append(iAuto)
    return resDicts
# ------------------------------------------------------------------------------------------------


def getInstancesSeries(seriesID):
    allInstanceIds = json.loads(orthanc.RestApiGet(f"/series/{seriesID}/instances"))
    return allInstanceIds

def getSeriesStudy(studyID):
    return json.loads(orthanc.RestApiGet(f"/studies/{studyID}"))['Series']

def getInstancesStudy(studyID):
    instanceIDs = []
    for iSeries in getSeriesStudy(studyID):
        instanceIDs += getInstancesSeries(iSeries)
    return instanceIDs

# def writeOutSeriesIDToFile(seriesID): # For testing
#     with open(f'{config["ORTHANC_AUTOMATION_DATA"]}/uro_out.txt', 'w') as fid:
#         fid.write(seriesID)

def getInstanceSaveFile(instanceID, rootDir):
    metadata = json.loads(orthanc.RestApiGet(f'/instances/{instanceID}'))
    metaSer = json.loads(orthanc.RestApiGet(f'/series/{metadata["ParentSeries"]}'))
    seNum = metaSer["MainDicomTags"]["SeriesNumber"]
    seDate = metaSer["MainDicomTags"]["SeriesDate"]
    seUID = metaSer["MainDicomTags"]["SeriesInstanceUID"]
    return os.path.join(rootDir, f'SE{seNum}-{seDate}-{seUID}', f'{metadata["MainDicomTags"]["SOPInstanceUID"]}.dcm')

# def getDownloadDirSeries(seriesID):
#     metadata = json.loads(orthanc.RestApiGet(f'/series/{seriesID}'))
#     metaPat = json.loads(orthanc.RestApiGet(f'/studies/{metadata["ParentStudy"]}'))
#     name = metaPat["PatientMainDicomTags"]["PatientName"].split('^')[0]
#     patientDir = os.path.join(DOWNLOAD_DIR, f'{metaPat["PatientMainDicomTags"]["PatientID"]}-{name}')
#     seriesOutDir = f'{patientDir}-SE{metadata["MainDicomTags"]["SeriesNumber"]}-{metadata["MainDicomTags"]["SeriesDate"]}-{metadata["MainDicomTags"]["SeriesInstanceUID"]}'
#     return seriesOutDir

def getDownloadDirStudy(studyID, prefix=''):
    metaPat = json.loads(orthanc.RestApiGet(f'/studies/{studyID}'))
    name = metaPat["PatientMainDicomTags"]["PatientName"].split('^')[0]
    prefix_ = prefix+'_' if len(prefix) > 0 else prefix
    patientDir = os.path.join(DOWNLOAD_DIR, f'{prefix_}{metaPat["PatientMainDicomTags"]["PatientID"]}-{name}')
    return patientDir

def getQueuedDir(studyID):
    downloadDir = getDownloadDirStudy(studyID)
    return downloadDir.replace(DOWNLOAD_DIR, QUEUED_DIR)

def changeOwnership(directory, userName, groupName):
    os.system(f"chown -R {userName}:{groupName} {directory}")

def writeOutStudyToDirectory(studyID, prefix='', FORCE=False):
    downloadDIR = getDownloadDirStudy(studyID, prefix) # Downloading
    queuedDIR = getQueuedDir(studyID)
    if os.path.isdir(queuedDIR):
        if FORCE:
            logger.warning(f"Removing {queuedDIR} to rewrite {studyID}")
            shutil.rmtree(queuedDIR)
        else:
            logger.warning(f"{studyID} already exists - not written out")
            return queuedDIR
    logger.info(f"Begin writing out study {studyID}")
    instances = getInstancesStudy(studyID)
    os.makedirs(downloadDIR, exist_ok=True)
    for instanceId in instances:
        instanceSaveFile = getInstanceSaveFile(instanceId['ID'], downloadDIR)
        os.makedirs(os.path.split(instanceSaveFile)[0], exist_ok=True)
        dicom = instanceToPyDicom(instanceId['ID'])
        dicom.save_as(instanceSaveFile, write_like_original=True)
        #
    logger.info(f"Finished writting {studyID}")
    os.rename(downloadDIR, queuedDIR)
    logger.info(f"Moved {downloadDIR} to {queuedDIR}")
    changeOwnership(queuedDIR, USERID, GROUPID)
    logger.info(f"Set ownership of {queuedDIR} to {USERID}:{GROUPID}")
    logger.info(f"WRITTEN: {queuedDIR}")
    return queuedDIR

def instanceToPyDicom(instanceID):
    f = orthanc.GetDicomForInstance(instanceID)
    # Parse it using pydicom
    dicom = pydicom.dcmread(io.BytesIO(f))
    return dicom


# def confirmSeriesWrittenOut(seriesID, destinationDir):
#     metadata = json.loads(orthanc.RestApiGet(f'/series/{seriesID}'))
#     nInstances = len(metadata['Instances'])
#     logger.info(f'COUNT: Expect {nInstances} instances -> list dir count = {len(os.listdir(destinationDir))}')
#     return len(os.listdir(destinationDir)) == nInstances

# def isSeriesDescription(seriesID, matchStr):
#     metadata = json.loads(orthanc.RestApiGet(f'/series/{seriesID}'))
#     try:
#         seriesDescription = metadata["MainDicomTags"]["SeriesDescription"]
#     except KeyError:
#         return False
#     return matchStr.lower() in seriesDescription.lower()

# def isUrography(seriesID):
#     metadata = json.loads(orthanc.RestApiGet(f'/series/{seriesID}'))
#     try:
#         seriesDescription = metadata["MainDicomTags"]["SeriesDescription"]
#         seriesNumber = int(metadata["MainDicomTags"]["SeriesNumber"])
#     except KeyError:
#         return False
#     return seriesDescription.endswith("(time)") and (seriesNumber < 100)

# def isUrographyPDF(seriesID):
#     metadata = json.loads(orthanc.RestApiGet(f'/series/{seriesID}'))
#     try:
#         seriesDescription = metadata["MainDicomTags"]["SeriesDescription"]
#         seriesNumber = int(metadata["MainDicomTags"]["SeriesNumber"])
#     except KeyError:
#         return False
#     return seriesDescription.endswith("ResultsPDF")

# ================================================================================================================
# def AutoPipelineOnStableSeries(seriesID, FORCE=False):
#     # TODO read master.json and get all ID  and action stuff
#     # tf = isSeriesDescription(seriesID, SERIES_CONTAINS_STR)
#     tf = isUrography(seriesID)
#     if tf:
#         print(f'Have new series {seriesID}. Is UROGRAPHY: {tf}')
#         outputDir = writeOutSeriesToDirectory(seriesID, FORCE)
#         if confirmSeriesWrittenOut(seriesID, outputDir): # Checks file count vs count in Orthanc
#             orthanc.RestApiDelete(f'/series/{seriesID}')
#             return 0
#         else:
#             # In this case - hopefully get some more dicoms and then force the IS_STABLE flag again
#             # Or at least not delete and can manually write (in case there was a writting problem)
#             return 1
#     tf2 = isUrographyPDF(seriesID)
#     if tf2:
#         print(f'Have new series {seriesID}. Is UROGRAPHYPDF: {tf2}')
#         orthanc.RestApiPost('/modalities/PACS/store', seriesID)
#         # orthanc.RestApiDelete(f'/series/{seriesID}')
#         # return 0
#     return 10 # if is not URO - still success

def AutoPipelineOnStableStudy(studyID, FORCE=False):
    resDicts = checkAutomationScriptsForStudy(studyID)
    for iResDict in resDicts:
        writeOutStudyToDirectory(studyID, iResDict['ID'], FORCE=FORCE)
    # if tf:
    #     print(f'Have new series {seriesID}. Is UROGRAPHY: {tf}')
    #     outputDir = writeOutSeriesToDirectory(seriesID, FORCE)
    #     if confirmSeriesWrittenOut(seriesID, outputDir): # Checks file count vs count in Orthanc
    #         orthanc.RestApiDelete(f'/series/{seriesID}')
    #         return 0
    #     else:
    #         # In this case - hopefully get some more dicoms and then force the IS_STABLE flag again
    #         # Or at least not delete and can manually write (in case there was a writting problem)
    #         return 1
    # tf2 = isUrographyPDF(seriesID)
    # if tf2:
    #     print(f'Have new series {seriesID}. Is UROGRAPHYPDF: {tf2}')
    #     orthanc.RestApiPost('/modalities/PACS/store', seriesID)
    #     # orthanc.RestApiDelete(f'/series/{seriesID}')
    #     # return 0
    return 0 # if is not URO - still success
            
# ================================================================================================================


# def ManualCallURO(output, uri, **request):
#     if request['method'] == 'GET':
#         # Retrieve the series ID from the regular expression (*)
#         seriesId = request['groups'][0]
#         result = AutoPipelineOnStableSeries(seriesId, FORCE=True)
#         if result == 0:
#             output.AnswerBuffer("SUCCESS: Pipeline initiated - you may close this page", 'text/plain')
#         elif result == 10:
#             output.AnswerBuffer("This series was not identified as a Urography series. If you are sure it is, please contact Fraser with examID and series number.", 'text/plain')
#         else:
#             output.AnswerBuffer("Oh no! Error encountered: please contact Fraser (fraser.callaghan@kispi.uzh.ch OR 3130)", 'text/plain')
#     else:
#         output.SendMethodNotAllowed('GET')

def OnChange(changeType, level, resource):
    if changeType == orthanc.ChangeType.ORTHANC_STARTED:
        pass
        # allSeriesIds = json.loads(orthanc.RestApiGet("/series"))
        # for seriesId in allSeriesIds:
        #     AutoPipelineOnStableSeries(seriesId, FORCE=False)

    elif changeType == orthanc.ChangeType.ORTHANC_STOPPED:
        pass

    # everytime a new study is received, we shall check it then process
    elif changeType == orthanc.ChangeType.STABLE_STUDY:
        try: 
            AutoPipelineOnStableStudy(resource, FORCE=True)
            # Force true so that if paused and then restarted then will overwrite
        except Exception as e: # Catch all general exceptions and debug
            logger.critical(e)

    # # everytime a new series is received, we shall check it then process
    # elif changeType == orthanc.ChangeType.STABLE_SERIES:
    #     AutoPipelineOnStableSeries(resource, FORCE=True)
    #     # Force true so that if paused and then restarted then will overwrite


# ================================================================================================================
#   MAIN
# ================================================================================================================
# add two restful callbacks

# (1) Add button on series labelled "Send series to Urography pipeline"
#        This button calls href: '/uropipeline/' + seriesID
#        This href is linked back to function here: ManualCallURO
# orthanc.RegisterRestCallback('/uropipeline/(.*)', ManualCallURO)  # (*)
# # here add the actual button
# with open("/python/extend-explorer.js", "r") as f:
#     orthanc.ExtendOrthancExplorer(f.read())

# (2) Register a callback to the OnChange signal
#       When ever a change occurs then "OnChange" function called
#       If the change is what we want (a stable series) then check if is URO and kick off pipeline
orthanc.RegisterOnChangeCallback(OnChange)

# This is ensure set up correctly
initStorage()
