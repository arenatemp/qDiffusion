import random
import sys
from typing import *

from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, Qt, QObject, QThread, QAbstractListModel, QByteArray, QModelIndex, QTimer, QVariant
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlDriver

class Database(QObject):
    notification = pyqtSignal(str)
    instance = None
    def __init__(self, parent):
        super().__init__(parent)
        self.db = QSqlDatabase.addDatabase("QSQLITE", "database")
        self.db.setConnectOptions("QSQLITE_OPEN_URI;QSQLITE_ENABLE_SHARED_CACHE")
        self.db.setDatabaseName("file::memory:")
        self.db.open()
        Database.instance = self

    @pyqtSlot(str)
    def onNotification(self, table):
        self.notification.emit(table)

class Connection(QObject):
    notification = pyqtSignal(str)
    def __init__(self, parent):
        super().__init__(parent)
        self.db = None

    def connect(self):
        name = f"db_{random.randint(0, 2**32)}"
        db = QSqlDatabase.cloneDatabase("database", name)
        db.open()
        db.driver().notification[str].connect(Database.instance.onNotification)
        Database.instance.notification.connect(self.relayNotification)

        self.db = db

    def enableNotifications(self, table):
        self.db.driver().subscribeToNotification(table)
        
    def doQuery(self, q):
        if type(q) == str:
            query = QSqlQuery(self.db)
            query.prepare(q)
            q = query
        
        while not q.exec():
            if q.lastError().nativeErrorCode() == "6":
                QThread.msleep(10)
            else:
                print(q.lastQuery(), q.boundValues(), q.lastError().text())
                break
        return q

    @pyqtSlot(str)
    def relayNotification(self, table):
        self.notification.emit(table)


class Sql(QAbstractListModel):
    queryChanged = pyqtSignal()
    def __init__(self, parent):
        super().__init__(parent)

        self.results = []

        self.conn = Connection(self)
        self.conn.connect()
        self.conn.notification.connect(self.onNotification)

        self.errored = False
        self.currentQuery = ""
        self.fieldNames: Dict[int, QByteArray] = {}

        self.reloadTimer = QTimer(self)
        self.reloadTimer.setSingleShot(True)
        self.reloadTimer.timeout.connect(self.reload)
        
    @pyqtProperty('QString', notify=queryChanged)
    def query(self):
        return self.currentQuery

    @query.setter
    def query(self, value):
        self.setQuery(value)

    def setQuery(self, value):
        self.currentQuery = value
        if not value:
            self.reset()
            self.queryChanged.emit()
            return

        q = self.conn.doQuery(self.currentQuery)
        self.errored = q.lastError().isValid()
        if self.errored:
            self.reset()
            self.queryChanged.emit()
            return

        newResults = []
        while q.next():
            newResults += [q.record()]
        q.finish()

        self.updateResults(newResults)
        self.queryChanged.emit()
        self.roleNames()
    
    def updateResults(self, newResults):
        def find(a, b):
            for i, e in enumerate(a):
                if e == b:
                    return i
            return -1

        if newResults:
            self.updateFieldNames(newResults[0])
        else:
            self.fieldNames = {}
        
        if len(self.results) == 0 or len(newResults) == 0:
            self.beginResetModel()
            self.results = newResults
            self.endResetModel()
            return

        i = 0
        while newResults and i < len(self.results):
            if self.results[i] == newResults[0]:
                newResults.pop(0)
                i += 1
                continue

            srcIdx = find(self.results[i:], newResults[0])
            dstIdx = find(newResults, self.results[i])
            if srcIdx == -1 and dstIdx == -1:
                self.beginRemoveRows(QModelIndex(), i, len(self.results)-1)
                self.results = self.results[:i]
                self.endRemoveRows()
                break
            elif srcIdx > 0:
                self.beginRemoveRows(QModelIndex(), i, i+srcIdx-1)
                self.results = self.results[:i] + self.results[i+srcIdx:]
                self.endRemoveRows()
        
            if dstIdx > 0:
                self.beginInsertRows(QModelIndex(), i, i+dstIdx-1)
                self.results = self.results[:i] + newResults[:dstIdx] + self.results[i:]
                self.endInsertRows()
                newResults = newResults[dstIdx:]
                i += dstIdx

        if newResults:
            self.beginInsertRows(QModelIndex(), i, i+len(newResults)-1)
            self.results += newResults
            self.endInsertRows()

    def data(self, index, role):
        value = QVariant()
        if role > Qt.UserRole:
            column = role - Qt.UserRole - 1
            row = index.row()
            if row < len(self.results):
                value = self.results[row].value(column)
        return value

    def updateFieldNames(self, record):
        self.fieldNames = {}
        for i in range(len(record)):
            self.fieldNames[Qt.UserRole + i + 1] = QByteArray(("sql_" + record.fieldName(i)).encode("utf-8"))

    def roleNames(self):
        return self.fieldNames

    def rowCount(self, parent):
        return len(self.results)

    def reset(self):
        self.beginResetModel()
        self.fieldNames = {}
        self.results = []
        self.endResetModel()

    @pyqtSlot(str)
    def onNotification(self, table):
        if table in self.currentQuery:
            if not self.reloadTimer.isActive():
                self.reloadTimer.start(random.randint(50,150))

    @pyqtSlot()
    def reload(self):
        self.setQuery(self.currentQuery)