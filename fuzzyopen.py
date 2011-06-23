# -*- coding: utf-8 -*-

import kate
import os
import re

from PyKDE4.kio import KDirLister
from PyKDE4.kdecore import KUrl, KMimeType, KConfig
from PyKDE4.kdeui import KIconLoader
from PyQt4 import uic
from PyQt4.QtCore import Qt, pyqtSignature
from PyQt4.QtGui import QDialog, QListWidgetItem, QIcon, QItemDelegate, QTextDocument, QStyle, QApplication

from settings import SettingsDialog


class HtmlItemDelegate(QItemDelegate):
	def __init__(self, parent):
		QItemDelegate.__init__(self, parent)
		self.document = QTextDocument(self)
		self.document.setDocumentMargin(0)
		self.hl_color = QApplication.palette().highlight().color()
		self.hl_color = ",".join( [`self.hl_color.red()`, `self.hl_color.green()`, `self.hl_color.blue()`] )
	
	def drawDisplay(self, painter, option, rect, text):
		point = rect.topLeft()
		painter.translate(point)
		if option.state & QStyle.State_Selected:
			text = "<div style='background-color: rgb(%s)'>%s</div>" % (self.hl_color, text)
		self.document.setHtml(text)
		self.document.drawContents(painter)
		painter.translate(-point)


class FuzzyOpen(QDialog):
	reason = ""
	recursion = 0
	maxRecursion = 3

	def __init__(self, parent=None, connections={}):
		QDialog.__init__(self, parent)
		self.setModal(True)
		uic.loadUi(os.path.join( os.path.dirname(__file__), "fuzzyopen.ui" ), self)
		self.hideProgress()
		self.iconLoader = KIconLoader()
		self.btnSettings.setIcon( QIcon(self.iconLoader.loadIcon("configure", KIconLoader.Small)) )
		
		self.config = KConfig("katefuzzyopenrc")
		configPaths = self.config.group("ProjectPaths")
		self.projectPaths = []
		for key in configPaths.keyList():
			path = configPaths.readPathEntry(key,"")
			if not path.endswith("/"):
				path += "/"
			self.projectPaths.append( path )
		
		configFilters = self.config.group("Filters")
		self.setIncludeFilters( configFilters.readEntry("include", "") )
		self.setExcludeFilters( configFilters.readEntry("exclude", "~$,\.bak$,/\.") )
		
		self.listUrl.setItemDelegate( HtmlItemDelegate(self.listUrl) )
			
		self.urls = []
		self.dirList = []
		self.lister = KDirLister()
		self.lister.newItems.connect(self.kioFiles)
		self.lister.completed.connect(self.kioFinished)
	
	def exec_(self):
		self.reset()
	
		katerect = kate.mainInterfaceWindow().window().rect()
		diarect = self.rect()
		diarect.moveCenter( katerect.center() )
		self.move( diarect.topLeft() )
	
		url = kate.activeDocument().url()
	
		self.project = False
		pi = 0
		while pi < len(self.projectPaths) and not self.project:
			if url.url().startswith( self.projectPaths[pi] ):
				self.project = self.projectPaths[pi]
			else:
				pi += 1
	
		for doc in kate.documentManager.documents():
			self.addFileUrl(doc.url(), "Open document")
	
		dirUrl = None
		if self.project:
			self.reason = "In project %s" % self.project
			self.recursion = 0
			dirUrl = KUrl(self.project)
		else:
			self.reason = "Same path of %s" % url.fileName()
			self.lister.setMimeExcludeFilter(["inode/directory"])
			dirUrl = url.upUrl()
	
		self.showProgress(dirUrl.url())
		self.lister.openUrl(dirUrl)
		return QDialog.exec_(self)
	
	def setIncludeFilters(self, filters):
		if filters:
			self.includeFilters = filters.split(",")
		else:
			self.includeFilters = []
	
	def setExcludeFilters(self, filters):
		if filters:
			self.excludeFilters = filters.split(",")
		else:
			self.excludeFilters = []

	def showProgress(self, text):
		self.lblProgress.setText(text)
		self.lblProgress.show()

	def hideProgress(self):
		self.lblProgress.hide()

	def reset(self):
		self.urls = []
		self.txtFilter.setText("")
		self.txtFilter.setFocus()
		self.listUrl.clear()
		self.lister.stop()
		self.lister.clearMimeFilter()

	def addFileUrl(self, url, reason=None):
		if url not in self.urls:
			mime = KMimeType.findByUrl(url)[0]
			item = QListWidgetItem()
			path = url.url()
			if self.project and path.startswith(self.project):
				path = path[ len(self.project): ]
			item.setWhatsThis(path)
			item.setText( "<b>%s</b>: <i>%s</i>" % ( url.fileName(), path ) )
			if reason:
				item.setToolTip(reason)
			item.setIcon( QIcon(self.iconLoader.loadMimeTypeIcon(mime.iconName(), KIconLoader.Small)) )
			self.listUrl.addItem(item)
			if url.fileName().find( self.txtFilter.text() ) < 0:
				self.listUrl.setItemHidden(item, True)
			self.urls.append(url)
			
			self.refreshFilter()
	
	def refreshFilter(self):
		self.on_txtFilter_textEdited( self.txtFilter.text() )

	def on_txtFilter_textEdited(self, s):
		firstMatch = -1
		pattern = re.compile( ".*".join( [re.escape(c) for c in s] ) )
		for i in range(self.listUrl.count()):
			matched = pattern.search(self.listUrl.item(i).whatsThis())
			if matched and firstMatch<0:
				firstMatch = i
			self.listUrl.setItemHidden(self.listUrl.item(i), matched is None)
		self.listUrl.setItemSelected(self.listUrl.item(firstMatch), True)
	
	def on_txtFilter_keyPressed(self, event):
		selected = self.listUrl.selectedItems()
		if selected:
			current_index = self.listUrl.row(selected[0])
		else:
			current_index = -1
		
		increment = 0
		if event.key() == Qt.Key_Up:
			increment = -1
		elif event.key() == Qt.Key_Down:
			increment = 1
		
		if increment != 0:
			current_index += increment
			while 0 <= current_index < self.listUrl.count():
				if self.listUrl.isRowHidden(current_index):
					current_index += increment
				else:
					self.listUrl.setItemSelected(self.listUrl.item(current_index), True)
					current_index = -1
			

	def on_txtFilter_returnPressed(self):
		if len(self.listUrl.selectedItems())>0:
			self.on_listUrl_itemActivated( self.listUrl.selectedItems()[0] )

	def on_listUrl_itemActivated(self, item):
		self.close()
		i = self.listUrl.row(item)
		if 0 <= i < len(self.urls):
			url = self.urls[i]
			kate.mainInterfaceWindow().activateView( kate.documentManager.openUrl(url) )

	@pyqtSignature("")
	def on_btnSettings_clicked(self):
		settingsDialog = SettingsDialog(kate.activeDocument().url(), self)
		settingsDialog.txtIncludePatterns.setText( ",".join(self.includeFilters) )
		settingsDialog.txtExcludePatterns.setText( ",".join(self.excludeFilters) )
		for path in self.projectPaths:
			settingsDialog.listProjectPaths.addItem(path)
		
		if settingsDialog.exec_():
			configPaths = self.config.group("ProjectPaths")
			for key in configPaths.keyList():
				configPaths.deleteEntry(key)
			self.projectPaths = []
			i = 0
			while i < settingsDialog.listProjectPaths.count():
				item = settingsDialog.listProjectPaths.item(i)
				configPaths.writePathEntry("path%s" % i, item.text())
				self.projectPaths.append(item.text())
				i += 1
			
			configFilters = self.config.group("Filters")
			includeFilters = settingsDialog.txtIncludePatterns.text()
			self.setIncludeFilters( includeFilters )
			configFilters.writeEntry( "include", includeFilters )
				
			excludeFilters = settingsDialog.txtExcludePatterns.text()
			self.setExcludeFilters( excludeFilters )
			configFilters.writeEntry( "exclude", excludeFilters )
			
			self.config.sync()

	def kioFiles(self, itemlist):
		for ifile in itemlist:
			url = ifile.url()
			
			path = url.url()
			if not path.endswith("/"):
				path += "/"
			
			
			if self.includeFilters:
				matched = False
				i = 0
				while not matched and i < len(self.includeFilters):
					try:
						if re.search(self.includeFilters[i], path):
							matched = True
					except re.error:
						pass
					i += 1
				if not matched:
					return
			
			for excludeFilter in self.excludeFilters:
				try:
					if re.search(excludeFilter, path):
						return
				except re.error:
					pass
				
			
			if ifile.isDir():
				if self.recursion<self.maxRecursion:
					self.dirList.append((self.recursion+1, url))
			else:
				mime = KMimeType.findByUrl(url)[0]
				if mime.name().startswith("text/") or mime.name()=="application/octet-stream" or "text/plain" in mime.parentMimeTypes():
					self.addFileUrl(url, self.reason)
				else:
					print mime.name(), url.fileName()
	
	def kioFinished(self):
		if self.dirList:
			self.recursion, dirUrl = self.dirList.pop()
			self.showProgress(dirUrl.url())
			self.lister.openUrl(dirUrl)
		else:
			self.hideProgress()

dialog = None

@kate.action('Fuzzy Open', shortcut="Meta+t", menu="File")
def fuzzyOpen():
	global dialog
	if dialog is None:
		dialog = FuzzyOpen(kate.mainWindow())
	dialog.exec_()