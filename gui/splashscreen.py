import sys
sys.path.append("..")

from sosangel_0_2.gui import filedialog

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QRect

from pyqtgraph import GraphicsLayoutWidget
import pyqtgraph as pg
import numpy as np
import re
import datetime

class SplashScreen:
    
    def __init__(self):
        
        self.title = 'SOSAngel'
        self.fileDialog = filedialog.FileDialog()
        self.path = ""
        
        self.initialize()
        
    def initialize(self):
        
        app = QApplication([])
        app.setApplicationName("SOSAngel")
        
        self.path = self.fileDialog.initialize() 
        print(self.path)
        
        sys.exit(app.exec_())