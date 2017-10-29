import os
import nltk
import sys       
import re
import datetime
import time
import codecs
import json
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd

class ReportFile:
    
    """Class
        
        Creates a basic ReportFile Object which would be used as a baseline object to be parsed for data throughout the library.
            
    """
    
    """Functions 
        
        walk(string toGet)
            -toGet is a string which could be either of "files" or "dirs"
            -returns a list of the path of the files or directories
        
        getFileCount()
            -returns the number of files in each of the main parent directories
       
        parseRsyslog()
            -parses the rsyslog.conf to get all the log file locations
            -returns a list of dicts which have the corresponding logfile names and data
            
        parseRsyslogFile(string location)
            -parses the given rsyslog file as called upon by parseRsyslog()
            -returns a dict with corresponding pathname and the logs associated to those files
            
        parseJournallog()
            -parses Journal Logs similarly as compared to Rsyslog files. 
            -returns a list of dictionaries of the file parsed.
            
        pasedAudit()
            -parses the audit logs as well as the audit log commmands fired by the sosreport binary
            -returns a list of dictionaries base d on the files it has parsed
    
    """
    
    def __init__(self,path):
        
        self.path = path
        
    def walk(self,toGet):
        
        fileList = []
        
        if toGet is "files" or "dirs":
            try:                    
                for root,dirs,files in os.walk(self.path):
                    if toGet == "files":
                        for name in files:
                            fileList.append(os.path.join(root,name))
                    elif toGet == "dirs":
                        for name in dirs:
                            fileList.append(os.path.join(root,name))
                            
            except:
                print("Error Ocurred : "+sys.exc_info()[0],file=sys.stderr)
                raise
        else:
            print("Please enter one of the following options : 'files' | 'dirs' ")
            
        return fileList
    
    def getFileCount(self):
 
        count = 0
        mainFolders = []
        folderFileCount = []

        mainStrs = [".*/sys$",
                    ".*/lib$",
                    ".*/usr$",
                    ".*/var$",
                    ".*/proc$",
                    ".*/boot$",
                    ".*/root$",
                    ".*/etc$",
                    ".*/sos_commands$",
                    ".*/sos_reports$",
                    ".*/sos_logs$",
                    ".*/lib64$"]
        
        try:
            for r in mainStrs:
                for d in self.walk("dirs"):
                    pattern = re.compile(r)
                    if pattern.match(d):
                        mainFolders.append(d)
                        folderFileCount.append(0)                        
        except:
            print("Error Ocurred : "+sys.exc_info()[0],file=sys.stderr)
            raise
        
        try:
            for di in range(len(mainFolders)):
                for f in self.walk("files"):
                    if mainFolders[di] in f:
                        folderFileCount[di] = folderFileCount[di] + 1
        except:
            print("Error Ocurred : "+sys.exc_info()[0],file=sys.stderr)
            raise

        try:
            fileCountTable = dict(zip(mainFolders,folderFileCount))
        except:
            print("Error Ocurred : "+sys.exc_info()[0],file=sys.stderr)
            raise
        
        return fileCountTable
    
    def parseRsyslogFile(self,location): #Parse individual rsyslog 
        
        messages = []
        messageLogFiles = []
        
        for f in self.walk("files"):
            try:
                if re.match(".*"+location+"(-?).*",f):
                    messageLogFiles.append(f)
            except:
                print("Error at parseRsyslogFile ( "+location+" "+f+" )")
        for f in messageLogFiles:
            
            #messageDict = {"path":f,"log":[]}
            #messages = []
            
            with codecs.open(f,"r",encoding='utf-8',errors='ignore') as logfile:
                print("Parsing RSYSLOGFile "+f+" ...........")    
                if re.match(".*boot(-?).*.log",f):
                    readBracket = 0
                    readMessage = 0
                    
                    for line in (logfile.readlines()):
                        lineDict = {"statuscode":"",
                                    "color":"",
                                    "message":""}
                        l= line.strip().split(" ")
                        for listEntry in l:
                            if listEntry == '':
                                l.remove('')
                        for i in range(len(l)):        
                            if (len(l[i])) > 0:
                                if l[i][-4:-1] == "31m":
                                    lineDict["color"] = "red"
                                    lineDict["statuscode"]=l[1]
                                    string = " ".join(word for word in l)
                                    lineDict["message"] = string
                                   
                                elif l[i][-3:-1] == "32":
                                    lineDict["color"] = "green"
                                    lineDict["statuscode"]=l[1]
                             
                                if len(l[i])>0 and l[i][-1] == "]":
                                    string = " ".join(word for word in l[i-1:-1])
                                    lineDict["message"] = string
                            
                        if len(lineDict["color"]) == 0:
                            lineDict["color"] = "none"
                            string = " ".join(word for word in l)
                            lineDict["message"] = string
                        
                        messages.append(lineDict)
                                                    
                else:
                    for line in (logfile.readlines()):
                        l = line.strip().split(" ")
                        for listEntry in l:
                            if listEntry == '':
                                l.remove('')
                        lineDict = {"timestamp":0,
                                    "host":"",
                                    "process":"",
                                    "message":""}
                        
                        year = datetime.datetime.now().year
                        try:
                            month = time.strptime(l[0],'%b').tm_mon
                            day = l[1]
                            t = l[2]
                            ts = str(day)+"-"+str(month)+"-"+str(year)+" "+str(t)

                            lineDict["timestamp"] = datetime.datetime.strptime(ts,"%d-%m-%Y %H:%M:%S").timestamp()
                            lineDict["host"] = l[3]
                            lineDict["process"] = l[4][:(len(l[4])-1)]
                            lineDict["message"] = ' '.join(l[i] for i in range(5,len(l)))
                            messages.append(lineDict)
                        except:
                            print("error in Parsing " + str(l))
            return messages  
    
    def parseRsyslog(self): #Parse Complete rsyslog 
        
        confFile = ""
        rsyslogConfMacros = [] #Macros defined in rsyslog.conf
        rsyslogConfLogs = [] #Log File locations defined in rsyslog.conf
        rsyslogRet = {"macros":[],"logs":[]}
                
        for f in self.walk("files"):
            if re.match(".*etc/rsyslog.conf.*",f):
                confFile = f
        print("Parsing RSYSLOG ............ ")
        with codecs.open(confFile,"r",encoding='utf-8',errors='ignore') as file:
            rsyslogConf = file.readlines()       
        
        for l in rsyslogConf:
            if l[0] == "$":
                string = ""
                commentMode = 0
                for i in range(len(l)):
                    if l[i] is "#":
                        commentMode = 1
                    if not commentMode:
                        string = string + l[i]
                rsyslogConfMacros.append(string)
            typeLoc = {"type":"","location":"","data":[]}    
            if l[0] != "$" and l[0] != "#":
                if l != "\n":
                    l = l.strip().split(" ")
                    typeLoc["type"] = l[0]
                    typeLoc["location"] = l[-1]
                    rsyslogConfLogs.append(typeLoc)
                       
        rsyslogRet["macros"] = rsyslogConfMacros
        rsyslogRet["logs"] = rsyslogConfLogs
        
        for i in range(len(rsyslogRet["logs"])):
            loc = rsyslogRet["logs"][i]["location"]
            rsyslogRet["logs"][i]["data"] = self.parseRsyslogFile(loc)
            
        return rsyslogRet
    
    def parseJournalLog(self):
        
        jfiles = []
        messageList = []
        
        for f in self.walk("files"):
            if re.match(".*journal((\.log)|(ctl_)).*",f):
                jfiles.append(f)
        jfiles = list(set(jfiles))        
        
        for f in jfiles:            
            if "--no-pager" in f:
                if "--output_verbose" in f: #Get the output in the Verbose JournalCtl Logs
                    messageLogFiles = []
                    
                    for file in self.walk("files"):
                        if re.match(".*"+f+"(-?).*",file):
                            messageLogFiles.append(f)
                    
                    for file in messageLogFiles:
                        messageDict = {"location":file,"logs":[]}
                        with codecs.open(file,"r",encoding='utf-8',errors='ignore') as logfile:
                            descVerbose = {"info":"","timestamp":"","verbose":[]}
                            for line in (logfile.readlines()):
                                l = line.strip().split(" ")
                                for listEntry in l:
                                    if listEntry == '':
                                        l.remove('')
                                        
                                readDescription = 0 
                                if "-" not in l[0]:
                                    if len(l) == 5:
                                        if len(l[4]) > 60:
                                            messageDict["logs"].append(descVerbose)
                                            date = l[1]
                                            tim = l[2]
                                            ts = date+" "+tim
                                            timestamp = datetime.datetime.strptime(ts,"%Y-%m-%d %H:%M:%S.%f").timestamp()
        
                                            descVerbose = {"timestamp":timestamp,"info":l[-1],"verbose":[]}
                                            readDescription = 1
                                if not readDescription:
                                    l = ' '.join(word for word in l)
                                    l = l.strip().split("=")
                                    if len(l) == 2:
                                        l = {"type":l[0],"message":l[-1]}
                                        #if l["type"] == "SYSLOG_IDENTIFIER":
                                            #print(l["message"]) This is the main process the verbose log is referring to
                                    descVerbose["verbose"].append(l)
                    messageDict = messageDict["logs"][1:]                
                    messageList.append(messageDict)
                    
                else: # Get the output in all the other journalctl Commang logs in sos_commands/logs
                    messageLogFiles = []

                    for file in self.walk("files"):
                        if re.match(".*"+f+"(-?).*",file):
                            messageLogFiles.append(f)
                            
                    for file in messageLogFiles:
                        messageDict = {"location":file,"logs":[]}
                        with codecs.open(file,"r",encoding='utf-8',errors='ignore') as logfile:                 
                            for line in (logfile.readlines()):
                                l = line.strip().split(" ")
                                for listEntry in l:
                                    if listEntry == '':
                                        l.remove('')
                                if "-" not in l[0]:
                                    lineDict = {"timestamp":0,
                                                "host":"",
                                                "process":"",
                                                "message":""}

                                    year = datetime.datetime.now().year
                                    month = time.strptime(l[0],'%b').tm_mon
                                    day = l[1]
                                    t = l[2]
                                    ts = str(day)+"-"+str(month)+"-"+str(year)+" "+str(t)
                                    lineDict["timestamp"] = datetime.datetime.strptime(ts,"%d-%m-%Y %H:%M:%S").timestamp()
                                    lineDict["host"] = l[3]
                                    lineDict["process"] = l[4][:(len(l[4])-1)]
                                    lineDict["message"] = ' '.join(l[i] for i in range(5,len(l)))
                                    messageDict["logs"].append(lineDict)                                    
                        messageList.append(messageDict)
                        
        return messageList

    def parseAudit(self):
        
        afiles = []
        messageList = []
        
        for f in self.walk("files"):
            if re.match(".*audit((\.log)|(ctl(_?))).*",f):
                afiles.append(f)
                
        for file in afiles:
            with codecs.open(file,"r",encoding='utf-8',errors='ignore') as logfile:
                messageDict = {"path":file,"logs":[]}
                
                if re.match(".*audit(ctl(_?)).*",file):
                    print("")
                    
                elif re.match(".*audit(\.log).*",file):
                    for l in logfile.readlines():
                        match = re.match(r"type=(?P<type>\w+) msg=audit\((?P<timestamp>.*):.*\):",l)
                        remove = re.search(r"type=(\w+) msg=audit\((.*)\):",l)
                        subfinal = re.split(" ?",l[:remove.start()] + l[remove.end():])
                        newDict = {}
                        for entry in subfinal:
                            m = re.match("(?P<key>.*)=(?P<value>.*)",entry)
                            if m:
                                d = m.groupdict()
                                newDict[d["key"]]=d["value"]
                        newDict["auditinfo"] = match.groupdict()        
                        messageDict["logs"].append(newDict)
            messageList.append(messageDict)
        return messageList
                    
    def orderLogs(self):
        
        RSYSLOG = self.parseRsyslog()
        AUDIT = self.parseAudit()
        JOURNAL = self.parseJournalLog()
        
        """
            not considering the following files while ordering the logs together :-
            boot.log
              
        """
        """
            timestampLog  
            {
                timestamp : 0.0
                logs :[
                    {
                        source : #journal, audit, rsyslog
                        process : {
                            name : #name of the process
                            pid : #Process id
                        }#Process name #need to find out naming convention for these
                        messages : []
                    }
                    .
                    .
                    .
                ]
            }
        """
        
        timestampLogs = []
        timestampsRecorded = []
        
        for logsInstance in RSYSLOG["logs"]:
            if "boot.log" not in logsInstance["location"]:
                oldTimestamp = 0
                newTimestamp = 0
                
                timestampLog = {
                    "timestamp":0.0,
                    "logs":[]
                }
                for log in logsInstance["data"]:
                    
                    logDict = {
                        "source" : "RSYSLOG",
                        "process" : {
                            "name":"",
                            "pid":""
                        },
                        "message":""
                    }
                    newTimestamp = log["timestamp"]
                    timestampLog["timestamp"] = newTimestamp
                    proc = re.match("(?P<name>.*)\[(?P<pid>.*)\]",log["process"])
                    if proc:
                        proc = proc.groupdict()
                        logDict["process"]["name"] = proc["name"]
                        logDict["process"]["pid"] = proc["pid"]
                    else:
                        logDict["process"]["name"] = log["process"]
                        logDict["process"]["pid"] = "none"
                   
                    logDict["message"] = log["message"]
                
                    if newTimestamp == oldTimestamp:
                        timestampLog["logs"].append(logDict)
                    elif newTimestamp != oldTimestamp:
                        if oldTimestamp not in timestampsRecorded and oldTimestamp is not 0:
                            timestampsRecorded.append(oldTimestamp)
                        if newTimestamp not in timestampsRecorded:
                            timestampsRecorded.append(newTimestamp)
                        timestampLog = {
                            "timestamp":float(newTimestamp),
                            "logs":[]
                        }
                        timestampLog["logs"].append(logDict)
                    
                    oldTimestamp = newTimestamp
                    timestampLogs.append(timestampLog)
        del(RSYSLOG)
        
        for logs in AUDIT:
            logs = logs["logs"]
            for log in logs:
                logDict = {
                        "source" : "AUDIT",
                        "process" : {
                            "name":"",
                            "id":""
                        },
                        "message":""
                    }
                timestamp = log["auditinfo"]["timestamp"]
                logDict["process"]["name"] = log["auditinfo"]["type"] 
                
                if "pid" in log.keys():
                    logDict["process"]["pid"] = log["pid"]
                else:
                    logDict["process"]["pid"] = "none"
                logDict["message"] = json.dumps(log)
                
                if timestamp not in timestampsRecorded:
                    timestampLog = {
                            "timestamp":float(timestamp),
                            "logs":[]
                        }
                    timestampLog["logs"].append(logDict)
                    timestampLogs.append(timestampLog)
                else:
                    i = timestampLogs.index(timestamp)
                    timestampLogs[i]["logs"].append(logDict)
        del(AUDIT)
      
        for logss in JOURNAL:
            if str(type(logss)) == "<class 'list'>":
                print(logss)
            elif str(type(logss)) == "<class 'dict'>":
                logs = logss["logs"]
                for log in logs:
                    logDict = {
                            "source" : "JOURNAL",
                            "process" : {
                                "name":"",
                                "id":""
                            },
                            "message":""
                        }

                    if "verbose" not in log.keys():
                        timestamp = log["timestamp"]
                        proc = re.match("(?P<name>.*)\[(?P<pid>.*)\]",log["process"])
                        if proc:
                            proc = proc.groupdict()
                            logDict["process"]["name"] = proc["name"]
                            logDict["process"]["pid"] = proc["pid"]
                        else:
                            logDict["process"]["name"] = log["process"]
                            logDict["process"]["pid"] = "none"

                        logDict["message"] = log["message"]
                    if timestamp not in timestampsRecorded:
                        timestampLog = {
                                "timestamp":float(timestamp),
                                "logs":[]
                            }
                        timestampLog["logs"].append(logDict)
                        timestampLogs.append(timestampLog)
                        
                    else:
                        i = timestampsRecorded.index(timestamp)
                        timestampLogs[i]["logs"].append(logDict)
                    
        del(JOURNAL)
        
        return timestampLogs            
                    
    def orderProcesses(self):
        
        RSYSLOG = self.parseRsyslog()
        #AUDIT = self.parseAudit()
        #JOURNAL = self.parseJournalLog()
        
        """
        {
            name:"",
            instances:[
                {
                    timestamp:0.0,
                    processes:[
                    {
                        pid:"",
                        message:"" 
                    },
                    .
                    .
                    .
                }
                .
                .
                .
            ]
        }
        .
        .
        .
        
        """
        processDicts = []
        
        processesEncountered = []
        timestampsEncountered = []
        
        processDict = {"name":"","instances":[]}
        processInstance = {"timestamps":0.0,"processes":[]}
        pDict = {"pid":"","message":""}
        
        for logInstance in RSYSLOG["logs"]:
            if "boot.log" not in logInstance["location"]:
                if logInstance["data"]:
                    for log in logInstance["data"]:
                        proc = re.match("(?P<name>.*)\[(?P<pid>.*)\]",log["process"])
                        if proc:
                            proc = proc.groupdict()
                        else:
                            proc = {}
                            proc["name"] = log["process"]
                            proc["pid"] = "none"

                        if proc["name"] not in processesEncountered:
                            processesEncountered.append(proc["name"])
                            timestampsEncountered.append([])
                            timestampsEncountered[processesEncountered.index(proc["name"])].append(log["timestamp"])

                            processDict = {"name":proc["name"],"instances":[]}
                            processInstance = {"timestamp":log["timestamp"],"processes":[]} 
                            pDict = {"pid":proc["pid"],"message":log["message"]}

                            processInstance["processes"].append(pDict)
                            processDict["instances"].append(processInstance)
                            processDicts.append(processDict)

                        else:
                            for processDict in processDicts:
                                if processDict["name"] ==  proc["name"]:
                                    for processInstance in processDict["instances"]:
                                        if processInstance["timestamp"] == log["timestamp"]:
                                            pDict = {"pid":proc["pid"],"message":log["message"]}
                                            processInstance["processes"].append(pDict)
                                        else:
                                            tsEncountered = timestampsEncountered[processesEncountered.index(proc["name"])]
                                            if log["timestamp"] not in tsEncountered:
                                                tsEncountered.append(log["timestamp"])

                                                processInstance = {"timestamp":log["timestamp"],"processes":[]}
                                                pDict = {"pid":proc["pid"],"message":log["message"]}

                                                processInstance["processes"].append(pDict)
                                                processDict["instances"].append(processInstance)
                            
        return processDicts
                    
        
    def parseSARFiles(self):

        print("Parsing SARFiles ..............")
        sarFiles = []

        for f in self.walk("files"):
            if re.match(".*sar.*((?!\.xml).)",f) and ".xml" not in f:
                sarFiles.append(f)
                sarFiles = list(set(sarFiles))
        SARs = []
        restarts = []
        for sar in sarFiles:
            with codecs.open(sar,"r",encoding='utf-8',errors='ignore') as sarFile:
                nextReport = 0
                fileHeader = ""
                date = ""
                currentIndex = []
                currentContent = []
                for line in sarFile.readlines():
                    lineList = [l for l in line.strip().split(" ") if l != ""]
                    readingReport = 0
                    currentHeaders = []
                    
                    if "Linux" in lineList:
                        fileHeader = lineList
                        for dat in fileHeader:
                            if re.match(".*(.*)/(.*)/(.*).*",dat):
                                
                                dat = dat[1:]
                                dat = dat.strip().split("/")
                                dat[-1] = "20"+dat[-1]
                                dat = "/".join(dat)
                                date = dat
                                
                    if nextReport == 1:
                        if len(currentIndex) != 0 and len(currentContent) !=0:
                            SARs.append({"sarContent":currentContent,"sarIndex":currentIndex})
                        currentIndex= lineList
                        currentContent = []
                        nextReport = 0
                    elif fileHeader is not "" and len(lineList) != 0 and date != "":
                        if re.match("(.*):(.*):(.*)",lineList[0]):
                            ts = date+" "+lineList[0]
                            ts = datetime.datetime.strptime(ts,'%m/%d/%Y %H:%M:%S')
                            ts = time.mktime(ts.timetuple())
                            lineList[0] = ts
                        currentContent.append(tuple(lineList))
                        
                    if len(lineList) == 0:
                        nextReport = 1
                    else:
                        nextReport=0
        return SARs
        
    def parseSAR(self):
        
        print("Redefining structure for SAR Reports ..............")
        
        SARs = self.parseSARFiles()
        mainIndices = []
        correspondingContent = []
        
        readyToPlot = []
        
        for SAR in SARs:
            content = SAR["sarContent"]
            indices = SAR["sarIndex"]
            parsedForPlot = {}
            for index in indices:
                elements = []
                for element in content:
                    elements.append(element[indices.index(index)])
                if re.match("(.*):(.*):(.*)",index):
                    index = "timestamp"
                parsedForPlot[index] = elements
            readyToPlot.append(parsedForPlot)
       
        return readyToPlot
                    
    def parseDMIDECODE(self):
        
        print("Parsing General Information .............")
        
        dmidecodeLocations = [
            ".*dmidecode.*", #DMIDECODE
            ".*sos_commands/kernel.dmidecode.*"
        ]
        
        dmidecodeFiles = []
        extracts = []
        
        for f in self.walk("files"):
            if re.match(dmidecodeLocations[0],f):
                dmidecodeFiles.append(f)
                dmidecodeFiles = list(set(dmidecodeFiles))
        
        for f in dmidecodeFiles:
            with codecs.open(f,"r",encoding='utf-8',errors='ignore') as dmiFile:
                encounteredBreak = False
                infoExtract = []
                startReading = False
                for line in (dmiFile.readlines()):
                    if "Handle" not in line:
                        line = line.strip().split("\t")
                        if "BIOS Information" in line[0]:
                            startReading = True
                        if startReading:
                            print(line[0])
                            if len(line[0]) == 0 and len(line) == 1:
                                encounteredBreak = True
                                if len(infoExtract) != 0:
                                    extracts.append(infoExtract)
                                    infoExtract = [] 
                            else:
                                infoExtract.append(" ".join(line))
                            
        for extract in extracts:
            print(extract)
                            
                    
                    
                    
                    
    