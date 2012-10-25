# -*- coding: utf-8 -*-
import kate
import os
import re

from PyKDE4.kio import KDirLister
from PyKDE4.kdecore import KUrl, KMimeType, KConfig
from PyKDE4.kdeui import KIconLoader
from PyQt4 import uic
from PyQt4.QtCore import Qt, pyqtSignature, QObject, pyqtSignal
from PyQt4.QtGui import QDialog, QListWidgetItem, QIcon, QItemDelegate, QTextDocument, QStyle, QApplication

from settings import SettingsDialog


class HtmlItemDelegate(QItemDelegate):
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)
        self.document = QTextDocument(self)
        self.document.setDocumentMargin(0)
        self.hl_color = QApplication.palette().highlight().color()
        self.hl_color = ",".join([repr(self.hl_color.red()), repr(self.hl_color.green()), repr(self.hl_color.blue())])

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

    def __init__(self, parent=None, connections={}):
        self.urls = []
        self.projectPaths = []

        QDialog.__init__(self, parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), "fuzzyopen.ui"), self)
        self.setModal(True)
        self.listUrl.setItemDelegate(HtmlItemDelegate(self.listUrl))
        self.hideProgress()

        self.iconLoader = KIconLoader()
        self.btnSettings.setIcon(QIcon(self.iconLoader.loadIcon("configure", KIconLoader.Small)))
        self.btnRefresh.setIcon(QIcon(self.iconLoader.loadIcon("view-refresh", KIconLoader.Small)))

        self.config = KConfig("katefuzzyopenrc")
        configPaths = self.config.group("ProjectPaths")
        for key in configPaths.keyList():
            path = configPaths.readPathEntry(key, "")
            if not path.endswith("/"):
                path += "/"
            self.projectPaths.append(path)

        configFilters = self.config.group("Filters")
        self.lister = DirLister()
        self.lister.fileFound.connect(self.listerFileFound)
        self.lister.directoryChanged.connect(self.listerDirChanged)
        self.lister.completed.connect(self.listerCompleted)
        self.lister.setIncludeFilters(configFilters.readEntry("include", ""))
        self.lister.setExcludeFilters(configFilters.readEntry("exclude", "~$\n\.bak$\n/\."))

    def showEvent(self, event):
        katerect = kate.mainInterfaceWindow().window().rect()
        diarect = self.rect()
        diarect.moveCenter(katerect.center())
        self.move(diarect.topLeft())

        self.reset()
        self.list()

    def getProjectUrl(self, url):
        for path in self.projectPaths:
            if url.url().startswith(path):
                return path
        return False

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

    def list(self):
        url = kate.activeDocument().url()
        self.project = self.getProjectUrl(url)

        for doc in kate.documentManager.documents():
            self.addFileUrl(doc.url(), "Open document")

        if self.project:
            self.reason = "In project %s" % self.project
            self.rootPath = KUrl(self.project)
        else:
            self.reason = "Same path of %s" % url.fileName()
            self.rootPath = url.upUrl()

        self.lister.list(self.rootPath, recurse=self.project != False)

    def addFileUrl(self, url, reason=None):
        if url not in self.urls:
            mime = KMimeType.findByUrl(url)[0]
            path = url.url()
            filename = url.fileName()

            item = QListWidgetItem()
            if self.project and path.startswith(self.project):
                path = path[len(self.project):]
                item.setWhatsThis(path)
                item.setText("<b>%s</b>: <i>%s</i>" % (filename, path))
            else:
                item.setWhatsThis(filename)
                item.setText("<b>%s</b>" % filename)
            if reason:
                item.setToolTip(reason)
            item.setIcon(QIcon(self.iconLoader.loadMimeTypeIcon(mime.iconName(), KIconLoader.Small)))
            self.listUrl.addItem(item)

            if url.fileName().find(self.txtFilter.text()) < 0:
                self.listUrl.setItemHidden(item, True)
            self.urls.append(url)

            self.refreshFilter()

    def refreshFilter(self):
        self.on_txtFilter_textEdited(self.txtFilter.text())

    def on_txtFilter_textEdited(self, s):
        firstMatch = -1
        pattern = re.compile(".*".join([re.escape(c) for c in s]), re.I)
        for i in range(self.listUrl.count()):
            matched = pattern.search(self.listUrl.item(i).whatsThis())
            if matched and firstMatch < 0:
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
        if len(self.listUrl.selectedItems()) > 0:
            self.on_listUrl_itemActivated(self.listUrl.selectedItems()[0])

    def on_listUrl_itemActivated(self, item):
        self.lister.stop()
        self.close()
        i = self.listUrl.row(item)
        if 0 <= i < len(self.urls):
            url = self.urls[i]
            kate.mainInterfaceWindow().activateView(kate.documentManager.openUrl(url))

    @pyqtSignature("")
    def on_btnSettings_clicked(self):
        settingsDialog = SettingsDialog(kate.activeDocument().url(), self)
        settingsDialog.txtIncludePatterns.setPlainText("\n".join([r.pattern for r in self.lister.includeFilters]))
        settingsDialog.txtExcludePatterns.setPlainText("\n".join([r.pattern for r in self.lister.excludeFilters]))
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
            includeFilters = settingsDialog.txtIncludePatterns.toPlainText()
            self.lister.setIncludeFilters(includeFilters)
            configFilters.writeEntry("include", includeFilters)

            excludeFilters = settingsDialog.txtExcludePatterns.toPlainText()
            self.lister.setExcludeFilters(excludeFilters)
            configFilters.writeEntry("exclude", excludeFilters)

            self.config.sync()

    @pyqtSignature("")
    def on_btnRefresh_clicked(self):
        url = self.rootPath.url()
        for k in self.lister.cache.keys():
            if k.startswith(url):
                del self.lister.cache[k]
        self.reset()
        self.list()

    def listerFileFound(self, url):
        QApplication.processEvents()
        self.addFileUrl(url, self.reason)

    def listerDirChanged(self, url):
        self.showProgress(url.url())

    def listerCompleted(self):
        self.hideProgress()


class DirLister(QObject):
    fileFound = pyqtSignal("KUrl")
    directoryChanged = pyqtSignal("KUrl")
    completed = pyqtSignal()

    recursion = 0
    maxRecursion = 10

    def __init__(self):
        QObject.__init__(self)
        self.cache = {}
        self.kio = KDirLister()
        self.kio.newItems.connect(self.kioFiles)
        self.kio.completed.connect(self.kioCompleted)
        self.includeFilters = []
        self.excludeFilters = []

    def stop(self):
        self.kio.stop()

    def setIncludeFilters(self, filters):
        self.includeFilters = []
        for filter in filters.splitlines():
            if filter:
                try:
                    self.includeFilters.append(re.compile(filter))
                except re.error:
                    pass

    def setExcludeFilters(self, filters):
        self.excludeFilters = []
        for filter in filters.splitlines():
            if filter:
                try:
                    self.excludeFilters.append(re.compile(filter))
                except re.error:
                    pass

    def validMime(self, mime):
        if mime.name() == "application/octet-stream":
            return True

        if mime.name().startswith("text/"):
            return True

        for parentMime in mime.parentMimeTypes():
            if parentMime.startswith("text/"):
                return True

        return False

    def list(self, url, recurse=True):
        self.recursion = 0 if recurse else self.maxRecursion
        self.dirStack = []
        self.cachedOpenUrl(url)

    def cachedOpenUrl(self, url):
        self.cacheUrl = url.url()
        if self.cacheUrl in self.cache:
            self.kioFiles(self.cache[self.cacheUrl])
            self.kioCompleted()
        else:
            self.directoryChanged.emit(url)
            self.kio.openUrl(url)

    def kioCompleted(self):
        if self.dirStack:
            self.recursion, url = self.dirStack.pop()
            self.cachedOpenUrl(url)
        else:
            self.completed.emit()

    def kioFiles(self, itemlist):
        if type(itemlist) != list:
            urlList = []
            for item in itemlist:
                urlList.append(dict(url=item.url().url(), isDir=item.isDir()))
            self.cache[self.cacheUrl] = urlList

        urls = []

        for ifile in itemlist:
            if type(ifile) == dict:
                url = KUrl(ifile["url"])
                isDir = ifile["isDir"]
            else:
                url = ifile.url()
                isDir = ifile.isDir()

            path = url.url()
            if isDir and not path.endswith("/"):
                path += "/"

            if self.includeFilters:
                matched = False
                i = 0
                while not matched and i < len(self.includeFilters):
                    if self.includeFilters[i].search(path):
                        matched = True
                    i += 1
                if not matched:
                    continue

            if self.excludeFilters:
                matched = False
                for excludeFilter in self.excludeFilters:
                    if excludeFilter.search(path):
                        matched = True
                        break
                if matched:
                    continue

            if isDir:
                if self.recursion < self.maxRecursion:
                    self.dirStack.append((self.recursion + 1, url))
            else:
                mime = KMimeType.findByUrl(url)[0]
                if self.validMime(mime):
                    urls.append(url)

        urls = sorted(urls, lambda a, b: -1 if len(a.url()) < len(b.url()) else 1)

        for url in urls:
            self.fileFound.emit(url)


dialog = None


@kate.action('Fuzzy Open', shortcut="Meta+t", menu="File")
def fuzzyOpen():
    global dialog
    if dialog is None:
        dialog = FuzzyOpen(kate.mainWindow())
    dialog.open()
