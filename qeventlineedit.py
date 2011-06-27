# -*- coding: utf-8 -*-
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QLineEdit

class QEventLineEdit(QLineEdit):
    keyPressed = pyqtSignal("QKeyEvent")

    def keyPressEvent(self, event):
        self.keyPressed.emit(event)
        return QLineEdit.keyPressEvent(self, event)