# -*- coding: utf-8 -*-
"""
Created on Thu Feb 16 17:16:55 2017

@author: Paniker
"""

import sys
import random
import plotGUI
from PyQt4 import QtGui

app = QtGui.QApplication(sys.argv)

x = [i-5 for i in range(10)]
y = [round(random.random()*100)/100 for i in range(10)]
win1 = plotGUI.plot(x,y,'b-')
win1.show()

x = [i-5 for i in range(10)]
y = [round(random.random()*100)/100 for i in range(10)]

win2 = plotGUI.plot(x,y,'r--')
win2.show()

''' uncomment for IPYTHON console '''
#sys.exit(app.exec_())