import sys
sys.path.append("..")

from sosangel_0_2.parse import report

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QRect

from pyqtgraph import GraphicsLayoutWidget
import pyqtgraph as pg
import numpy as np
import re
import datetime


class GUI:

    def __init__(self,sosPath):

        
        self.sosReport = report.ReportFile(sosPath)
        self.sosReport.parseDMIDECODE()
        self.sars = self.sosReport.parseSAR()
        self.processes = self.sosReport.orderProcesses()
        self.initialize()
        
    def initialize(self):
        
        app = QApplication([])
        app.setApplicationName("SOSAngel")
        
        self.initializeData()
        self.initializeWidgets()
        
        sys.exit(app.exec_())
    
    def initializeData(self):
        print("Initializing Data")
        self.initializeProcessesData()
        self.initializeSARData()
        
    def initializeSARData(self):
        
        print("Initializing SAR Data for Plotting ..........")
        readingSARwithNominalStatistics = 0
        SARs = []
        for SAR in self.sars:
            print("-------------------------------------------------------------------")
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
        self.SARData = SARs
    def initializeProcessesData(self):
       
        print("Initializing Data for Processes ........")
        
        self.processNames = []
        self.processTimestamps = []
        self.processLengths = []
        
        for process in self.processes:
            self.processNames.append(process["name"])
            self.processTimestamps.append([i["timestamp"] for i in process["instances"]])
            self.processLengths.append([len(i["processes"]) for i in process["instances"]])
        
    def initializeWidgets(self):
        self.initializeProcessRiver()
        
    def initializeProcessRiver(self):
        print("Initializing ProcessRiver ........")
        
        dateTimeAxis = DateTimeAxis(orientation='bottom')
        processesAxis = ProcessesAxis(self.processNames,orientation='left')
        sarAxis = SARAxis(orientation='right')
        
        self.ProcessRiver = ProcessRiver(self.processNames,self.processTimestamps,self.processLengths,self.SARData,axisItems={'bottom':dateTimeAxis,'left':processesAxis,'right':sarAxis})
        self.ProcessRiver.show()
    

    
class ProcessRiver(pg.PlotWidget):
    
    def __init__(self,processNames,processTimestamps,processLengths,sarData,*args,**kwargs):
        pg.PlotWidget.__init__(self,*args,**kwargs)
        self.processNames = processNames
        self.processTimestamps = processTimestamps
        self.processLengths = processLengths
        self.SARData = sarData
        self.initialize()
        
    def initialize(self):
        self.initializeData()
        
    def initializeData(self):
        self.p1 = self.plotItem
        self.p2 = pg.ViewBox()
        self.p1.showAxis('right')
        self.p1.scene().addItem(self.p2)
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p1.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p1)
        
        self.p1.vb.sigResized.connect(self.updateViews)
        self.p1.vb.enableAutoRange(axis= pg.ViewBox.XYAxes, enable=True)
        
        self.processLogScatters = []
        self.sarPlots = []
        
        print("Parsing SAR Data for ProcessRiver ........")      
        for SAR in self.SARData:
            for SARDict in SAR:
                if SARDict["nominalKey"] is None:
                    timestamps = SARDict["values"]["timestamp"]
                    toPlot = {}
                    for key in SARDict["values"].keys():
                        if key != "timestamp":
                            toPlot[key] = SARDict["values"][key]
                            
                    for i in range(len(list(toPlot.keys()))):
                        curveItem = pg.PlotCurveItem(timestamps,toPlot[list(toPlot.keys())[i]],pen=i)
                        self.sarPlots.append({"name":list(toPlot.keys())[i],"plot":curveItem})
                        #self.p2.addItem(curveItem)
        
        print("Parsing Process Data for ProcessRiver ........")            
        for i in range(len(self.processNames)):
            spots =  [{'pos':(self.processTimestamps[i][j],i),'size':self.processLengths[i][j],'pen':i,'brush':i} for j in range(len(self.processTimestamps[i]))]
            scatterItem = pg.ScatterPlotItem(spots=spots)
            self.processLogScatters.append(scatterItem)
            self.p1.vb.addItem(scatterItem)
            
        
    def updateViews(self):
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
                    
        
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