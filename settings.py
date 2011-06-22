# -*- coding: utf-8 -*-

import os

from PyQt4.QtGui import QDialog, QIcon
from PyQt4.QtCore import pyqtSignature
from PyQt4 import uic
from PyKDE4.kio import KDirSelectDialog
from PyKDE4.kdeui import KIconLoader

class SettingsDialog(QDialog):
	__url = None

	def __init__(self, url, parent=None):
		QDialog.__init__(self, parent)
		self.setModal(True)
		uic.loadUi(os.path.join( os.path.dirname(__file__), "settings.ui" ), self)
		self.__url = url
		iconLoader = KIconLoader()
		self.btnAdd.setIcon( QIcon(iconLoader.loadIcon("list-add", KIconLoader.Small)) )
		self.btnDel.setIcon( QIcon(iconLoader.loadIcon("list-remove", KIconLoader.Small)) )
	
	@pyqtSignature("")
	def on_btnAdd_clicked(self):
		dirUrl = KDirSelectDialog.selectDirectory(self.__url, False, self)
		self.listProjectPaths.addItem(dirUrl.url())

	@pyqtSignature("")
	def on_btnDel_clicked(self):
		self.listProjectPaths.takeItem( self.listProjectPaths.currentRow() )