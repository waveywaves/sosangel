import sys
sys.path.append("..")

from sosangel.parse import report
from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget,QGridLayout,QVBoxLayout,QTextEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
import pyqtgraph as pg
from pyqtgraph.flowchart import Flowchart, Node

import datetime

TIMESTAMPSHAREDVALUES = []

class GUI(QMainWindow):
 
    def __init__(self,sosPath):
        super().__init__()
        self.title = 'SOS Angel'
        self.left = 0
        self.top = 0
        self.width = 700
        self.height = 500
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
 
        self.centralWidget = CentralWidget(self,sosPath)
        self.setCentralWidget(self.centralWidget)
         
        self.show()
    
class CentralWidget(QWidget):        
 
    def __init__(self, parent, sosPath):   
        super(QWidget, self).__init__(parent)
        
        self.sosReport = report.ReportFile(sosPath)
        #self.sosReport.parseDMIDECODE()
        #self.sars = self.sosReport.parseSAR()
        
        self.mappings = self.sosReport.parseLVM2()
        self.timestampLogs = self.sosReport.orderTimestamps()
        self.sars = self.sosReport.parseSAR()
        self.processes = self.sosReport.orderProcesses()
        self.layout = QVBoxLayout(self)
        
        self.initializeProcessesData()
        self.initializeTabs()
        
    def initializeProcessesData(self):
       
        print("Initializing Data for Processes ........")
        
        self.processNames = []
        self.processTimestamps = []
        self.processLengths = []
        
        for process in self.processes:
            self.processNames.append(process["name"])
            self.processTimestamps.append([i["timestamp"] for i in process["instances"]])
            self.processLengths.append([len(i["processes"]) for i in process["instances"]])
       
    def initializeTabs(self):
        # Initialize tab screen
        self.tabs = QTabWidget()
        
        self.mpathTab = mPathWidget(self,self.mappings)
        self.sarTab = SARVisualizerWidget(self,self.sars)
        self.logsTab = LogVisualizerWidget(self,self.processNames,self.processTimestamps,self.processLengths,self.timestampLogs)
        
        
        self.tabs.resize(700,500) 
        
        # Add tabs
        self.tabs.addTab(self.logsTab,"LOGS")
        self.tabs.addTab(self.sarTab,"System Activity")
        self.tabs.addTab(self.mpathTab,"MPath Viewer")
        # Add tabs to widget        
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

class LogVisualizerWidget(QWidget):

    def __init__(self,parent,processNames,processTimestamps,processLengths,timestampLogs):
        super(QWidget, self).__init__(parent)
        
        self.processNames = processNames
        self.processTimestamps = processTimestamps
        self.processLengths = processLengths
        self.timestampLogs = timestampLogs
        self.timestampToProcesses = []
        self.layout = QGridLayout(self)
        self.initialize()
    
    def initialize(self):
        
        self.logsCollective = QTabWidget()
        
        self.initializeTimestampLogsData()
        self.initializeVisualizationTabs()
        
        self.layout.addWidget(self.logsCollective)
        self.setLayout(self.layout)
        
    def initializeTimestampLogsData(self):
        
        print("Initializing Timestamp Log Data for Log Visualizer  ................")
        timestampToProcesses = {} 
       
        for process in self.processNames:
            timestampToProcesses[process] = {"pids":[],"timestamps":[],"logs":[]}
    
        for timestampLog in self.timestampLogs:
            ts = timestampLog["timestamp"]
            for log in timestampLog["logs"]:
                for process in self.processNames:
                    if log["process"]["name"] == process:
                        timestampToProcesses[process]["timestamps"].append(ts)
                        timestampToProcesses[process]["logs"].append(log["message"])
                        timestampToProcesses[process]["pids"].append(log["process"]["pid"])
        self.timestampToProcesses = timestampToProcesses
    
    def initializeVisualizationTabs(self):
 
        for i in range(len(self.processNames)):
            tsToPro = self.timestampToProcesses[self.processNames[i]]
            ins = LogVisualizerInstance(self,self.processNames[i],self.processTimestamps[i],self.processLengths[i],tsToPro)
            self.logsCollective.addTab(ins,self.processNames[i])
                      
class LogVisualizerInstance(QWidget):
    def __init__(self,parent,name,timestamps,values,tsToPro):
        super(QWidget, self).__init__(parent)
        
        self.name = name
        self.timestamps = timestamps
        self.values = values
        self.timestampToProcesses = tsToPro
        
        self.layout = QGridLayout(self)
        self.initialize()
        
    def initialize(self):
        
        dateTimeAxis = DateTimeAxis(orientation='bottom')
        processesAxis = ProcessesAxis([self.name],orientation='left')
        
        self.logsPlot = LogVisualizerPlot(self.name,self.timestamps,self.values,axisItems={'bottom':dateTimeAxis})  
        self.logsViewer = LogListingViewer(self,self.timestampToProcesses)      
        
        self.configViewer = QTextEdit(self)
        self.configViewer.setReadOnly(True)
        self.configViewer.setLineWrapMode(QTextEdit.NoWrap)
        
        font = self.logsViewer.font()
        font.setFamily("Courier")
        font.setPointSize(10)

        self.layout.addWidget(self.logsPlot,1,1,2,1)
        self.layout.addWidget(self.logsViewer,1,2,2,1)
        #self.layout.addWidget(self.configViewer,2,1,1,1)
        
    def mousePressEvent(self,event):
        global TIMESTAMPSHAREDVALUES
        self.logsViewer.setTimestamps()
        
class LogListingViewer(QTextEdit):
    
    def __init__(self,parent,tsToPro):
        super(QTextEdit, self).__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)
        
        self.timestampToProcesses = tsToPro
        self.timestamps = []
        self.logsToShow = []
        
        self.insertPlainText("\n".join(self.timestamps))
    
    def getLogsToShow(self):
        print("Getting Log Listing Viewer Logs ...........")
        self.logsToShow = []
        for timestamp in self.timestamps:
            for tsPro in self.timestampToProcesses["timestamps"]:
                if tsPro == timestamp:
                    string = "\n".join(list(set(self.timestampToProcesses["logs"])))
                    if string not in self.logsToShow:
                        self.logsToShow.append(string)
        
    def setTimestamps(self):
        self.timestamps = TIMESTAMPSHAREDVALUES
        
        self.clear()
        self.getLogsToShow()
        self.insertPlainText("\n".join(self.logsToShow))
        
class LogVisualizerPlot(pg.PlotWidget):
    def __init__(self,name,timestamps,values,*args,**kwargs):
        
        global TIMESTAMPSHAREDVALUES
        
        pg.PlotWidget.__init__(self,*args,**kwargs)
        self.name = name
        self.timestamps = timestamps
        self.values = values
        
        self.rangeX0 = 0
        self.rangeX1 = 0
        
        self.rangeXMid = self.rangeX0 + (self.rangeX1 - self.rangeX0)
        
        self.globaltimestampshared = TIMESTAMPSHAREDVALUES
        
        self.initialize()

    
    def initialize(self):
        
        self.observerLine = pg.PlotCurveItem()
        self.timestampsUnderObservation = []
        self.parallelValuesToTimestamp = []
        self.addItem(self.observerLine)
        
        self.selectedRegion = pg.LinearRegionItem()
        self.addItem(self.selectedRegion)
        self.selectedRegion.setRegion([min(self.timestamps),max(self.timestamps)])  
        
        self.setTitle(self.name)
        self.curveItem = pg.PlotCurveItem(self.timestamps,self.values,pen='b')
        self.addItem(self.curveItem)
        
    def mouseMoveEvent(self,event):
        
        self.xM = (event.x() - self.geometry().width()/2)
        self.yM =  (event.y() - self.geometry().height()/2)
        
        minVal = min(self.timestamps)
        maxVal = max(self.timestamps)
        
        if self.xM is not 0:#and self.yM > -95:
            self.rangeX0 = min(self.timestamps) + self.xM*200 - self.yM*400
            self.rangeX1 = max(self.timestamps) + self.xM*200 + self.yM*400
        self.rangeXMid = self.rangeX0 + (self.rangeX1 - self.rangeX0)/2
        
        self.selectedRegion.setRegion([self.rangeXMid-200,self.rangeXMid+200])  
        self.setXRange(self.rangeX0,self.rangeX1)
        self.timestampsUnderObservation = (between(self.timestamps,list(self.selectedRegion.getRegion())))
        self.parallelValuesToTimestamp = returnParallelValuesInList(self.timestampsUnderObservation,self.timestamps,self.timestamps)
        
    def mouseReleaseEvent(self,event):
        global TIMESTAMPSHAREDVALUES
        TIMESTAMPSHAREDVALUES = self.parallelValuesToTimestamp
        
class SARVisualizerWidget(QWidget):
    
    def __init__(self,parent,sars):
        super(QWidget, self).__init__(parent)
        self.sars = sars
        
        self.SARData = []
        self.indexAndMeasurers = []
        self.parsedSARstructures = []
        
        self.layout = QGridLayout(self)
        self.initialize()
            
    def initialize(self):
        
        self.SARData = self.initializeSARData()
        self.indexAndMeasurers = self.getSARStatListing()
        self.sarsCollective = QTabWidget()
        
        self.parsedSARstructures = self.parseSARstructures()
        self.initializeVisualizationTabs()
        
        self.layout.addWidget(self.sarsCollective)
        self.setLayout(self.layout)
        
    def initializeVisualizationTabs(self):
       
        for i in range(len(list(self.indexAndMeasurers.keys()))):
            dateTimeAxis = DateTimeAxis(orientation='bottom')
            ins = SARVisualizerInstance(list(self.indexAndMeasurers.keys())[i], self.indexAndMeasurers[list(self.indexAndMeasurers.keys())[i]],self.parsedSARstructures[i],axisItems={'bottom':dateTimeAxis})
            self.sarsCollective.addTab(ins,list(self.indexAndMeasurers.keys())[i].title())
    
    def parseSARstructures(self):
        
        print("Preparing SAR Structures for readability ................")
        
        titles = list(self.indexAndMeasurers.keys())
        titleToStats = [self.indexAndMeasurers[key] for key in self.indexAndMeasurers.keys()]
        statsToValues = [[] for i in titles]
        for i in range(len(list(self.indexAndMeasurers.keys()))):
            list(self.indexAndMeasurers.keys())[i]
        
        for sarList in self.SARData:
            for sar in sarList:
                if sar["nominalKey"] is  None:
                    for value in list(sar["values"].keys()):
                        for li in range(len(titleToStats)):
                            if value in titleToStats[li] and sar not in statsToValues[li]:
                                statsToValues[li].append(sar)
                                
        return statsToValues
                        
    def getSARStatListing(self):
        
        f = open("/home/vibhav/Desktop/Project/sosangel/gui/sar.txt")
        br = 0
        readStat = []
        allread = []
        statInfo = ""
        for line in f.readlines():
            line = line.strip().split(" ")
            if len(line[0]) == 0:
                br = 1
            else:
                br = 0

            if br == 1:
                allread.append(readStat)
                readStat = []
                br = 0
            else:
                readStat.append(" ".join(line))

        mainDict = {}        
        for l in allread:
            if len(l) != 0:
                mainDict[l[0]] = l[1:]

        return mainDict
    
    def initializeSARData(self):
        
        print("Initializing SAR Data for Plotting ..........")
        readingSARwithNominalStatistics = 0
        SARs = []
        for SAR in self.sars:
            print("-------------------------------------------------------------------")
            upperCaseKeyExists = False
            upperCaseKey = ""
            for key in SAR.keys():
                if key.isupper():
                    upperCaseKeyExists = True
                    upperCaseKey = key #CPU
                SARList = []
            if upperCaseKeyExists:
                nominalListingNames =list(set(SAR[upperCaseKey])) #[1,2,3,4,5,6,7,8]
                nominalListingNTV = [{} for name in nominalListingNames] #[{},{},{},{},{},{},{},{}]
                for name in nominalListingNames:
                    for key in SAR.keys():
                        for v in range(len(SAR[key])):
                            if name == SAR[upperCaseKey][v] and key != upperCaseKey:
                                if key in nominalListingNTV[nominalListingNames.index(SAR[upperCaseKey][v])].keys():
                                    if SAR["timestamp"][v] != "Average:" :
                                        nominalListingNTV[nominalListingNames.index(SAR[upperCaseKey][v])][key].append(float(SAR[key][v]))
                                    #else:
                                        #nominalListingNTV[nominalListingNames.index(SAR[upperCaseKey][v])][key].append(SAR[key][v])
                                else:
                                    nominalListingNTV[nominalListingNames.index(SAR[upperCaseKey][v])][key] = []
                                
                                #print(name,key,SAR[key][v])
                SARList.append({"nominalKey":upperCaseKey,"names":nominalListingNames,"values":nominalListingNTV})
            else:
                values = {}
                for key in SAR.keys():
                    for v in range(len(SAR[key])):
                        if key in values.keys():
                            if SAR["timestamp"][v] != "Average:":
                                values[key].append(float(SAR[key][v]))
                            #else:
                                #values[key].append(SAR[key][v])
                        else:
                            values[key] = []
                                
                SARList.append({"nominalKey":None,"names":None,"values":values})    
            SARs.append(SARList)
        return SARs
    
class SARVisualizerInstance(pg.PlotWidget):
    def __init__(self,name,statNames,sarData,*args,**kwargs):
        pg.PlotWidget.__init__(self,*args,**kwargs)
        
        self.title = name
        self.statNames = statNames
        self.sarData = sarData
        self.layout = QGridLayout(self)
        
        self.legend = pg.LegendItem()
        self.addItem(self.legend)
        
        self.initialize()
        
    def initialize(self):
        self.setTitle(self.title)
        self.initializePlot()
       
    def initializePlot(self):
        
        timestamps = []
        
        for sarData in self.sarData:

            timestamps = timestamps + sarData["values"]["timestamp"] 
            for k in range(len(list(sarData["values"].keys()))):
                if list(sarData["values"].keys())[k] is not "timestamp":
                    curveItem = pg.PlotCurveItem()
                    curveItem.setData(timestamps,sarData["values"][list(sarData["values"].keys())[k]],pen = k)
                    self.addItem(curveItem)
                    self.legend.addItem(curveItem,list(sarData["values"].keys())[k])
            self.setXRange(min(timestamps),max(timestamps))
        
        vb = self.plotItem.vb
        self.legend.setParentItem(vb)
        self.legend.anchor((0,0), (0,0))
        """
        self.additionalView = pg.ViewBox()
        self.addItem(self.additionalView)
        self.legend.setParentItem(self.additionalView)
        #self.legend.anchor(itemPos=(1,0), parentPos=(1,0), offset=(-10,10))
        self.legend.autoAnchor((10,-10))         
        """
class mPathWidget(QWidget):
    
    def __init__(self,parent,mappings):
        super(QWidget, self).__init__(parent)
        
        self.mappings = mappings
        self.initialize()
    
    def initialize(self):
        pvhistory = []
        lvhistory = []
        n=0
        fc = Flowchart(terminals={ 
                'in': {'io': 'out'},
                'op': {'io': 'in'}
                })

        nodeList = fc.nodes()
        fc.removeNode(nodeList['Input'])
        fc.removeNode(nodeList['Output'])

        for i in self.mappings["vgs"]:

            vgNode = Node(i, allowRemove=False, allowAddOutput=False)
            fc.addNode(vgNode, i, [0,n])
            Node.addTerminal(vgNode,'O', io = 'out', multi=True)
            Node.addTerminal(vgNode, 'I', io = 'in', multi=True)

            for j in self.mappings["mappings"]:
                if i == j[1]:
                    if j[2] not in lvhistory:              
                        lvNode = Node(j[2], allowRemove=False, allowAddOutput=False)
                        fc.addNode(lvNode, j[2], [200, n])
                        Node.addTerminal(lvNode,'I', io = 'in')
                        try:
                            fc.connectTerminals(vgNode['O'],lvNode['I'])
                        except:
                            pass
                            #cvar2 = Node.addOutput(vgNode)
                            #fc.connectTerminals(vgNode['Out'],cvar2)
                        
                        lvhistory.append(j[2])
                    else:
                        pass

                    if j[0] not in pvhistory:    
                        pvNode = Node(j[0], allowRemove=False, allowAddOutput=False)
                        fc.addNode(pvNode, j[0], [-400, n])
                        Node.addTerminal(pvNode,'O', io = 'out')
                        try:    
                            fc.connectTerminals(pvNode['O'],vgNode['I'])
                        except:
                            pass
                            #cvar1 = Node.addInput(vgNode)
                            #fc.connectTerminals(pvNode['Out'], cvar1)
                        
                        pvhistory.append(j[0])
                    else:
                        pass                    
                    n = n + 200
        #vgNode.ctrls['doubleSpin'].setValue(5)
        #lvNode = fc.createNode('PlotWidget', 'lv')

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(fc.widget())
        #fc.removeNode(fc, fc.Input)
        
class DateTimeAxis(pg.AxisItem):
    
    def __init__(self,  *args, **kwargs):
        pg.AxisItem.__init__(self,*args,**kwargs)
    
    def tickStrings(self, values, scale, spacing):
        
        strings = []
        
        try:
            strings = [datetime.datetime.fromtimestamp(val).strftime('%A \n %Y-%b-%d \n %H:%M:%S') for val in values]
        except:
            print("")
        return strings     
        
class ProcessesAxis(pg.AxisItem):       
    
    def __init__(self, processNames, *args, **kwargs): 
        pg.AxisItem.__init__(self,*args,**kwargs)
        self.processNames = processNames
        self.setTicks([[(i,self.processNames[i]) for i in range(len(self.processNames))]])

class SARAxis(pg.AxisItem):

    def __init__(self,  *args, **kwargs):
        pg.AxisItem.__init__(self,*args,**kwargs)
    def tickStrings(self, values, scale, spacing):
        strings = []
        try:
            strings = [str(float(val)) for val in values]
        except:
            print("")
        return strings

def returnParallelValuesInList(valueIndicesToFind,listToFindIn,parallelValuesToExtractFrom):
    indices = []
    returnValues = []
    for val in valueIndicesToFind:
        indices.append(listToFindIn.index(val))
    for i in indices:
        returnValues.append(parallelValuesToExtractFrom[i])
    
    returnValues = [val for val in returnValues]
    
    return returnValues    
        
def between(l1,lowhigh): #Function to find time values between two given values provided that they exist in a list 
    l2 = []
    for i in l1:
        if(i > lowhigh[0] and i < lowhigh[-1]):
            l2.append(i)
    return l2        
    