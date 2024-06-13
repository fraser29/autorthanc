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
import time

# ============ CONFIG ==============================================================================
auto_scripts_dir="/automation_scripts" # This is directory in docker file system - do not change
output_dir="/automation_output"
DOWNLOAD_DIR = output_dir
USERID = os.getenv("UID", '1000')
GROUPID = os.getenv("GID", '1000')
logfile = os.path.join(auto_scripts_dir, 'orthanc_automation.log')
DOWNLOAD = "DOWNLOAD"
FORWARD = "FORWARD"
DestinationModality = "DestinationModality"
DEBUG=True

# ============ LOGGING =============================================================================
logger = logging.getLogger(f"autorthanc")
if DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
fh = logging.FileHandler(logfile, encoding='utf-8')
fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-7s | %(name)s | %(message)s', 
                                  datefmt='%d-%b-%y %H:%M:%S'))
logger.addHandler(fh)
logger.info('===== START AUTORTHANC ===== ')
logger.debug(' :: RUNNING IN DEBUG MODE  ')


# -------------------------------------------------------------------------------------------------
def initStorage():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    logger.info('Autorthanc storage initiated.')


def writeDictionaryToJSON(fileName, dictToWrite):
    with open(fileName, 'w') as fp:
        json.dump(dictToWrite, fp, indent=4, sort_keys=True)
    return fileName

def parseJsonToDictionary(fileName):
    with open(fileName, 'r') as fid:
        myDict = json.load(fid)
    return myDict

def getAllAutomationDictionary(checkOn):
    """Return dictionaries parsed from json files found in 'auto_scripts_dir'

    Args:
        checkOn (str): type of stable action to check on (Study / Series)
    
    Return: list of dicts: dict is parsed from json - see automation_template.json
    """
    autoscripts = [os.path.join(auto_scripts_dir, i) for i in os.listdir(auto_scripts_dir) if \
                   (i.endswith('json') and (not i.startswith('master')) and (not 'template' in i))]
    autoDicts = []
    for iFile in autoscripts:
        try:
            iDict = parseJsonToDictionary(iFile)
            if iDict.get("CheckOn", "") != checkOn:
                continue
            if iDict.get("IsActive", False):
                iDict['ID'] = os.path.splitext(os.path.split(iFile)[1])[0]
                autoDicts.append(iDict)
        except json.decoder.JSONDecodeError:
            logger.error(f"{iFile} has incorrect format")
        except:
            logger.error(f"Error reading {iFile}")
    return autoDicts

def _doesMatchAutoDict(ID, autoDict, checkOn):
    if checkOn == "Study":
        return doesStudyMatchAutoDict(ID, autoDict)
    elif checkOn == "Series":
        return doesSeriesMatchAutoDict(ID, autoDict)
    return False

def doesSeriesMatchAutoDict(seriesID, autoDict):
    metaSeries = json.loads(orthanc.RestApiGet(f'/series/{seriesID}'))
    studyID = metaSeries["ParentStudy"]
    metaStudy = json.loads(orthanc.RestApiGet(f'/studies/{studyID}'))
    return _doesAutoDictMatchWithQuery(autoDict, 
                                       metaStudy=metaStudy,
                                       metaSeriesList=[metaSeries])

def doesStudyMatchAutoDict(studyID, autoDict):
    metaStudy = json.loads(orthanc.RestApiGet(f'/studies/{studyID}'))
    metaSeriesList = [json.loads(orthanc.RestApiGet(f'/series/{iSeries}')) for iSeries in metaStudy['Series']]
    return _doesAutoDictMatchWithQuery(autoDict, 
                                       metaStudy=metaStudy,
                                       metaSeriesList=metaSeriesList)

def _doesAutoDictMatchWithQuery(autoDict, metaStudy, metaSeriesList):
    metaPatient = json.loads(orthanc.RestApiGet(f'/patients/{metaStudy["ParentPatient"]}'))
    allTF = []
    for iTag in autoDict['Tags']:
        if iTag['Level'].lower() == 'patient':
            try:
                thisValue = metaPatient['MainDicomTags'].get(iTag['TagName'], 'NONE').lower()
                allTF.append(iTag['Value'].lower() in thisValue)
            except TypeError:
                return False
        elif iTag['Level'].lower() == 'study':
            try:
                thisValue = metaStudy['MainDicomTags'].get(iTag['TagName'], 'NONE').lower()
                allTF.append(iTag['Value'].lower() in thisValue)
            except TypeError:
                return False
        elif iTag['Level'].lower() == 'series':
            thisValues = [i['MainDicomTags'].get(iTag['TagName'], 'NONE').lower() for i in metaSeriesList]
            subTF = []
            for i in thisValues:
                try:
                    subTF.append(iTag['Value'].lower() in i)
                except TypeError:
                    pass
            allTF.append(any(subTF))
    return all(allTF)

def checkAutomationScripts(study_or_series_ID, checkOn):
    """Will retrun all json that match this study or series
    Args:
        study_or_series_ID (str): study_or_series_ID
        checkOn (str): type of stable action to check on: "Study" OR "Series"
    Returns:
        list: list of dictionaries with JSON information
    """
    allAutoScripts = getAllAutomationDictionary(checkOn)
    logger.debug(f"Found {len(allAutoScripts)} potential scripts for action in stable {checkOn} for resource: {study_or_series_ID}")
    resDicts = []
    for iAuto in allAutoScripts:
        if _doesMatchAutoDict(study_or_series_ID, iAuto, checkOn):
            logger.info(f"Processing {study_or_series_ID} for JSON: {iAuto['ID']}")
            resDicts.append(iAuto)
    logger.debug(f"Found {len(resDicts)} scripts matching for action in stable {checkOn} for resource: {study_or_series_ID}")
    return resDicts

def moveDirSrc_toDest(dirSrc, dirDest):
    for iSrc, _, files in os.walk(dirSrc):
        iDest = iSrc.replace(dirSrc, dirDest, 1)
        if not os.path.exists(iDest):
            os.makedirs(iDest)
        for file_ in files:
            src_file = os.path.join(iSrc, file_)
            dst_file = os.path.join(iDest, file_)
            if os.path.exists(dst_file):
                # in case of the src and dst are the same file
                if os.path.samefile(src_file, dst_file):
                    continue
                os.remove(dst_file)
            shutil.move(src_file, iDest)
    # finally remove the original
    shutil.rmtree(dirSrc)
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

def getInstanceSaveFile(instanceID, rootDir):
    metadata = json.loads(orthanc.RestApiGet(f'/instances/{instanceID}'))
    metaSer = json.loads(orthanc.RestApiGet(f'/series/{metadata["ParentSeries"]}'))
    seNum = metaSer["MainDicomTags"].get("SeriesNumber", "XX")
    seDate = metaSer["MainDicomTags"].get("SeriesDate", "UNKNOWN")
    seUID = metaSer["MainDicomTags"]["SeriesInstanceUID"]
    return os.path.join(rootDir, f'SE{seNum}-{seDate}-{seUID}', f'{metadata["MainDicomTags"]["SOPInstanceUID"]}.dcm')


def getStudyDescriptor(studyID):
    """Return pid-name-examid"""
    metaStudy = json.loads(orthanc.RestApiGet(f'/studies/{studyID}'))
    name = metaStudy["PatientMainDicomTags"].get("PatientName", "UNKNOWN^").split('^')[0]
    examid = metaStudy["MainDicomTags"].get("StudyID", "UNKNOWN")
    return f'{metaStudy["PatientMainDicomTags"]["PatientID"]}-{name}-EX{examid}'


def getSeriesDescriptor(seriesID):
    """Return pid-name-examid-seriesNum"""
    metaSeries = json.loads(orthanc.RestApiGet(f'/series/{seriesID}'))
    studyID = metaSeries["ParentStudy"]
    metaStudy = json.loads(orthanc.RestApiGet(f'/studies/{studyID}'))
    name = metaStudy["PatientMainDicomTags"].get("PatientName", "UNKNOWN^").split('^')[0]
    patID = metaStudy["PatientMainDicomTags"].get("PatientID", "NoPID")
    examid = metaStudy["MainDicomTags"].get("StudyID", "UNKNOWN")
    seNum = metaSeries["MainDicomTags"].get("SeriesNumber", "XX")
    return f'{patID}-{name}-EX{examid}-SE{seNum}'


def getDownloadDirStudy(studyID, rootDir):
    patientDir = os.path.join(rootDir, getStudyDescriptor(studyID))
    return patientDir

def getDownloadDirSeries(seriesID, rootDir):
    patientDir = os.path.join(rootDir, getSeriesDescriptor(seriesID))
    return patientDir

def changeOwnership(directory, uid, gid):
    try:
        logger.debug(f"Change ownership of {directory} to {uid}:{gid}")
        for root, dirs, files in os.walk(directory):
            for name in dirs:
                dir_path = os.path.join(root, name)
                os.chown(dir_path, uid, gid)
            for name in files:
                file_path = os.path.join(root, name)
                os.chown(file_path, uid, gid)
        os.chown(directory, uid, gid)
        logger.debug(f"Finished change of ownership of {directory} to {uid}:{gid}")
    except Exception as e: # Catch all general exceptions and debug
        logger.exception(f"During change of ownership for {directory}")

# def changeOwnership(directory, userName, groupName):
#     time.sleep(5.0)
#     os.system(f"chown -R {userName}:{groupName} {directory}")
#     time.sleep(5.0)

def writeOutSeriesToDirectory(seriesID, rootDir, FORCE=False):
    # TODO - CHECK
    if not os.path.isdir(rootDir):
        os.makedirs(rootDir, exist_ok=True)
    changeOwnership(rootDir, USERID, GROUPID)
    queuedDIR = getDownloadDirSeries(seriesID, rootDir) # Downloading
    seriesDesc = getSeriesDescriptor(seriesID)
    instances = getInstancesSeries(seriesID)
    return _writeOutInstances(instances=instances, 
                              destinationDir=queuedDIR,
                              descriptor=seriesDesc,
                              FORCE=FORCE)

def writeOutStudyToDirectory(studyID, rootDir, FORCE=False):
    if not os.path.isdir(rootDir):
        os.makedirs(rootDir, exist_ok=True)
    changeOwnership(rootDir, USERID, GROUPID)
    queuedDIR = getDownloadDirStudy(studyID, rootDir) # Downloading
    studyDesc = getStudyDescriptor(studyID)
    instances = getInstancesStudy(studyID)
    return _writeOutInstances(instances=instances, 
                              destinationDir=queuedDIR,
                              descriptor=studyDesc,
                              FORCE=FORCE)

def _writeOutInstances(instances, destinationDir, descriptor, FORCE=False):
    if os.path.isdir(destinationDir):
        if FORCE:
            logger.warning(f"{destinationDir} exists - appending / overwriting {descriptor}")
        else:
            logger.warning(f"{descriptor} already exists - not written out")
            return destinationDir
    downloadDIR = destinationDir+'.WORKING'
    logger.info(f"Begin writing out study {descriptor}")
    if not os.path.isdir(downloadDIR):
        os.makedirs(downloadDIR, exist_ok=True)
    changeOwnership(downloadDIR, USERID, GROUPID)
    for instanceId in instances:
        instanceSaveFile = getInstanceSaveFile(instanceId['ID'], downloadDIR)
        os.makedirs(os.path.split(instanceSaveFile)[0], exist_ok=True)
        dicom = instanceToPyDicom(instanceId['ID'])
        dicom.save_as(instanceSaveFile, write_like_original=True)
        #
    logger.info(f"Finished writting {descriptor}")
    if os.path.isdir(destinationDir):
        logger.info(f"{destinationDir} exists - deleting. ")
        shutil.rmtree(destinationDir)
        time.sleep(5.0)
    moveDirSrc_toDest(downloadDIR, destinationDir)
    # os.rename(downloadDIR, queuedDIR)
    logger.info(f"Moved {downloadDIR} to {destinationDir}")
    changeOwnership(destinationDir, USERID, GROUPID)
    logger.info(f"Set ownership of {destinationDir} to {USERID}:{GROUPID}")
    logger.info(f"DONE: WRITTEN: {destinationDir}")
    return destinationDir

def instanceToPyDicom(instanceID):
    f = orthanc.GetDicomForInstance(instanceID)
    # Parse it using pydicom
    dicom = pydicom.dcmread(io.BytesIO(f))
    return dicom

def sendSeriesToOtherModality(seriesID, remoteModality):
    originatorAET = os.getenv("ORTHANC__DICOM_AET")
    seDesc = getSeriesDescriptor(seriesID)
    logger.info(f"Moving {seDesc} from {originatorAET} to {remoteModality}")
    # TODO - CONFIRM
    orthanc.RestApiPost(f'/modalities/{remoteModality}/store', 
                        '{"Asynchronous": false,"Compress": true,"Permissive": true,"Priority": 0,"Resources": ["' + \
                            seriesID + '"],"Synchronous": false, "MoveOriginatorAet": "' + \
                                originatorAET + '", "MoveOriginatorID": ' + str(0) + ', "Permissive": true, "StorageCommitment": true}')
    logger.info(f"DONE: FORWARDED {seDesc} from {originatorAET} to {remoteModality}")

def sendStudyToOtherModality(studyID, remoteModality):
    originatorAET = os.getenv("ORTHANC__DICOM_AET")
    studyDesc = getStudyDescriptor(studyID)
    logger.info(f"Moving {studyDesc} from {originatorAET} to {remoteModality}")
    orthanc.RestApiPost(f'/modalities/{remoteModality}/store', 
                        '{"Asynchronous": false,"Compress": true,"Permissive": true,"Priority": 0,"Resources": ["' + \
                            studyID + '"],"Synchronous": false, "MoveOriginatorAet": "' + \
                                originatorAET + '", "MoveOriginatorID": ' + str(0) + ', "Permissive": true, "StorageCommitment": true}')
    logger.info(f"DONE: FORWARDED {studyDesc} from {originatorAET} to {remoteModality}")

def AutoPipelineOnStableStudy(studyID, FORCE):
    resDicts = checkAutomationScripts(studyID, "Study")
    for iResDict in resDicts:
        if iResDict.get("Action", "NONE") == DOWNLOAD:
            writeOutStudyToDirectory(studyID, rootDir=os.path.join(DOWNLOAD_DIR, iResDict['ID']), FORCE=FORCE)
        elif iResDict.get("Action", "NONE") == FORWARD:
            if DestinationModality in iResDict.keys():
                sendStudyToOtherModality(studyID, iResDict[DestinationModality])
        else:
            logger.warning(f"Unknow study action described by {iResDict['ID']} : {iResDict.get('Action', 'NONE')}")
    for iSeries in getSeriesStudy(studyID):
        try:
            AutoPipelineOnStableSeries(iSeries, FORCE=True)
        except Exception as e: # Catch all general exceptions and debug
            logger.exception(f"In STABLE_STUDY processing SERIES for studyID: {iSeries}")
            return 2
    return 0 
            
def AutoPipelineOnStableSeries(seriesID, FORCE):
    resDicts = checkAutomationScripts(seriesID, "Series")
    for iResDict in resDicts:
        if iResDict.get("Action", "NONE") == DOWNLOAD:
            writeOutSeriesToDirectory(seriesID, rootDir=os.path.join(DOWNLOAD_DIR, iResDict['ID']), FORCE=FORCE)
        elif iResDict.get("Action", "NONE") == FORWARD:
            if DestinationModality in iResDict.keys():
                sendSeriesToOtherModality(seriesID, iResDict[DestinationModality])
        else:
            logger.warning(f"Unknow study action described by {iResDict['ID']} : {iResDict.get('Action', 'NONE')}")
    return 0 
            
# ================================================================================================================

def OnChange(changeType, level, resource):
    if changeType == orthanc.ChangeType.ORTHANC_STARTED:
        pass

    elif changeType == orthanc.ChangeType.ORTHANC_STOPPED:
        pass

    # everytime a new study is received, we shall check it then process
    elif changeType == orthanc.ChangeType.STABLE_STUDY:
        logger.debug(f"Stable STUDY check begun on {resource}")
        try: 
            AutoPipelineOnStableStudy(resource, FORCE=True)
            # Force true so that if paused and then restarted then will overwrite
        except Exception as e: # Catch all general exceptions and debug
            logger.exception(f"In STABLE_STUDY for studyID: {resource}")
    
    elif changeType == orthanc.ChangeType.STABLE_SERIES:
        pass # TO REDUCE ACTIONS SHIFT THIS TO STABLE STUDY 
        # logger.debug(f"Stable SERIES check begun on {resource}")
        # try: 
        #     AutoPipelineOnStableSeries(resource, FORCE=True)
        #     # Force true so that if paused and then restarted then will overwrite
        # except Exception as e: # Catch all general exceptions and debug
        #     logger.exception(f"In STABLE_SERIES for studyID: {resource}")


def ForceAutoPipelineOnStableStudy(output, uri, **request):
    if request['method'] == 'GET':
        # Retrieve the instance ID from the regular expression (*)
        studyID = request['groups'][0]
        resDicts = checkAutomationScripts(studyID, "Study")
        output.AnswerBuffer(f"Running AutoPipelineOnStableStudy on {studyID}\n Results:\n{resDicts}", 'text/plain')
        AutoPipelineOnStableStudy(studyID, FORCE=True)
    else:
        output.SendMethodNotAllowed('GET')


# ================================================================================================================
#   MAIN
# ================================================================================================================
# add restful callbacks

# (1) Register a callback to the OnChange signal
#       When ever a change occurs then "OnChange" function called
#       If the change is what we want (a stable series) 
orthanc.RegisterOnChangeCallback(OnChange)

# (2) # add callback to 
orthanc.RegisterRestCallback('/forcestablesignal/(.*)', ForceAutoPipelineOnStableStudy)  # (*)
# add a "Force Automation Action" button in the Orthanc Explorer
with open("/scripts/extend-explorer.js", "r") as f:
    orthanc.ExtendOrthancExplorer(f.read())

# This is ensure set up correctly
initStorage()
