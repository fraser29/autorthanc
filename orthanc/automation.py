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

# ============ LOGGING =============================================================================
logger = logging.getLogger(f"autorthanc")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(logfile, encoding='utf-8')
fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-7s | %(name)s | %(message)s', 
                                  datefmt='%d-%b-%y %H:%M:%S'))
logger.addHandler(fh)
logger.info('===== START AUTORTHANC ===== ')


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

def getAllAutomationDictionary():
    """Return dictionaries parsed from json files found in 'auto_scripts_dir'
    
    Return: list of dicts: dict is parsed from json - see automation_template.json
    """
    autoscripts = [os.path.join(auto_scripts_dir, i) for i in os.listdir(auto_scripts_dir) if \
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


def checkAutomationScriptsForStudy(studyID):
    """Will retrun all json that match this study
    Args:
        studyID (str): study ID
    Returns:
        list: list of dictionaries with JSON information
    """
    allAutoScripts = getAllAutomationDictionary()
    resDicts = []
    for iAuto in allAutoScripts:
        if doesStudyMatchAutoDict(studyID, iAuto):
            logger.info(f"Processing {studyID} for JSON: {iAuto['ID']}")
            resDicts.append(iAuto)
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
    """Retrun pid-name-examid"""
    metaPat = json.loads(orthanc.RestApiGet(f'/studies/{studyID}'))
    name = metaPat["PatientMainDicomTags"].get("PatientName", "UNKNOWN^").split('^')[0]
    examid = metaPat["MainDicomTags"].get("StudyID", "UNKNOWN")
    return f'{metaPat["PatientMainDicomTags"]["PatientID"]}-{name}-{examid}'


def getDownloadDirStudy(studyID, rootDir):
    patientDir = os.path.join(rootDir, getStudyDescriptor(studyID))
    return patientDir


def changeOwnership(directory, userName, groupName):
    os.system(f"chown -R {userName}:{groupName} {directory}")
    time.sleep(5.0)

def writeOutStudyToDirectory(studyID, rootDir, FORCE=False):
    if not os.path.isdir(rootDir):
        os.makedirs(rootDir, exist_ok=True)
        changeOwnership(rootDir, USERID, GROUPID)
    queuedDIR = getDownloadDirStudy(studyID, rootDir) # Downloading
    downloadDIR = queuedDIR+'.WORKING'
    if os.path.isdir(queuedDIR):
        if FORCE:
            logger.warning(f"{queuedDIR} exists - appending / overwriting {getStudyDescriptor(studyID)}")
        else:
            logger.warning(f"{getStudyDescriptor(studyID)} already exists - not written out")
            return queuedDIR
    logger.info(f"Begin writing out study {getStudyDescriptor(studyID)}")
    instances = getInstancesStudy(studyID)
    if not os.path.isdir(downloadDIR):
        os.makedirs(downloadDIR, exist_ok=True)
        changeOwnership(downloadDIR, USERID, GROUPID)
    for instanceId in instances:
        instanceSaveFile = getInstanceSaveFile(instanceId['ID'], downloadDIR)
        os.makedirs(os.path.split(instanceSaveFile)[0], exist_ok=True)
        dicom = instanceToPyDicom(instanceId['ID'])
        dicom.save_as(instanceSaveFile, write_like_original=True)
        #
    logger.info(f"Finished writting {getStudyDescriptor(studyID)}")
    if os.path.isdir(queuedDIR):
        logger.info(f"{queuedDIR} exists - deleting. ")
        shutil.rmtree(queuedDIR)
        time.sleep(5.0)
    moveDirSrc_toDest(downloadDIR, queuedDIR)
    # os.rename(downloadDIR, queuedDIR)
    logger.info(f"Moved {downloadDIR} to {queuedDIR}")
    changeOwnership(queuedDIR, USERID, GROUPID)
    logger.info(f"Set ownership of {queuedDIR} to {USERID}:{GROUPID}")
    logger.info(f"DONE: WRITTEN: {queuedDIR}")
    return queuedDIR

def instanceToPyDicom(instanceID):
    f = orthanc.GetDicomForInstance(instanceID)
    # Parse it using pydicom
    dicom = pydicom.dcmread(io.BytesIO(f))
    return dicom

def sendStudyToOtherModality(studyID, remoteModality):
    originatorAET = os.getenv("ORTHANC__DICOM_AET")
    logger.info(f"Moving {getStudyDescriptor(studyID)} from {originatorAET} to {remoteModality}")
    orthanc.RestApiPost(f'/modalities/{remoteModality}/store', 
                        '{"Asynchronous": false,"Compress": true,"Permissive": true,"Priority": 0,"Resources": ["' + \
                            studyID + '"],"Synchronous": false, "MoveOriginatorAet": "' + \
                                originatorAET + '", "MoveOriginatorID": ' + str(0) + ', "Permissive": true, "StorageCommitment": true}')
    logger.info(f"DONE: FORWARDED {getStudyDescriptor(studyID)} from {originatorAET} to {remoteModality}")

def AutoPipelineOnStableStudy(studyID, FORCE=False):
    resDicts = checkAutomationScriptsForStudy(studyID)
    for iResDict in resDicts:
        if iResDict.get("Action", "NONE") == DOWNLOAD:
            writeOutStudyToDirectory(studyID, rootDir=os.path.join(DOWNLOAD_DIR, iResDict['ID']), FORCE=FORCE)
        elif iResDict.get("Action", "NONE") == FORWARD:
            if DestinationModality in iResDict.keys():
                sendStudyToOtherModality(studyID, iResDict[DestinationModality])
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
        try: 
            AutoPipelineOnStableStudy(resource, FORCE=True)
            # Force true so that if paused and then restarted then will overwrite
        except Exception as e: # Catch all general exceptions and debug
            logger.exception(f"In STABLE_STUDY for studyID: {resource}")


def ForceAutoPipelineOnStableStudy(output, uri, **request):
    if request['method'] == 'GET':
        # Retrieve the instance ID from the regular expression (*)
        studyID = request['groups'][0]
        resDicts = checkAutomationScriptsForStudy(studyID)
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
