#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import path
import shlex
from os.path import basename
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import (QFrame, QListWidget,
                             QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout,
                             QApplication, QListWidgetItem,)

def find_mount(location):
    location = path.Path(location)
    if location.parent.ismount() or location.parent == "/":
        return location.parent
    else:
        return find_mount(location.parent)

class CustomEntry(QListWidgetItem):
    """Un widget représentant une entrée custom"""
    def __init__(self, parent=0, name="", isoLocation="", permanent=True, loopbackLocation="", mountpoint="/"):
        QListWidgetItem.__init__(self, parent)
        self.setText(name)
        self.isoLocation = isoLocation
        if loopbackLocation:
            loopbackLocation = path.Path(mountpoint) / loopbackLocation[1:] # On vire le premier "/"
            self.loopbackContent = loopbackLocation.text()
        else: self.loopbackContent = ""
        self.permanent = permanent
        self.mountpoint = mountpoint
        if not permanent:
            brush = QBrush(QColor(255, 0, 0))
            self.setForeground(brush)
    
    def setIsoLocation(self, isoLocation):
        self.isoLocation = isoLocation
        self.setText(basename(isoLocation))
    
    def setPermanent(self, permanent):
        self.permanent = permanent
        if not permanent:
            brush = QBrush(QColor(255, 0, 0))
            self.setForeground(brush)
        else:
            brush = QBrush(QColor(0, 0, 0))
            self.setForeground(brush)
    
    def setLoopbackContent(self, loopbackContent):
        self.loopbackContent = loopbackContent
    
    def setMountPoint(self, mountpoint):
        self.mountpoint = mountpoint
    
    def getIsoLocation(self):
        return self.isoLocation
    
    def getPermanent(self):
        return self.permanent
    
    def getLoopbackContent(self):
        return self.loopbackContent
    
    def getMountPoint(self):
        return self.mountpoint

class CustomEditor(QFrame):
    """Classe permettant de modifier le fichier custom"""
    
    currentItemChanged = pyqtSignal(QListWidgetItem)
    
    def __init__(self, grubRep=""):
        QFrame.__init__(self)
        
        # Instanciation des variables
        self.grubRep = path.Path(grubRep)
        self.cache = {}
        
        ## Création des Widgets
        # Texte
        label = QLabel("Liste des entrées personnalisées")
        label.setAlignment(Qt.AlignHCenter)
        # Liste des entrées
        self.CustomEntriesList = QListWidget()
        self.CustomEntriesList.currentItemChanged.connect(self.emitSignal)
        # Boutons
        add = QPushButton("Ajouter")
        remove = QPushButton("Supprimer")
        add.clicked.connect(self.addNewItem)
        remove.clicked.connect(self.removeCurrentItem)
        
        ## Création des Layout
        # Boutons
        buttons = QHBoxLayout()
        buttons.addWidget(add)
        buttons.addWidget(remove)
        # Layout principal
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.CustomEntriesList)
        vbox.addLayout(buttons)
        
        # Affichage de l'interface
        self.setLayout(vbox)
        
        # Récupération des entrées
        if self.grubRep:
            self.getCustomEntries()
    
    def getCustomEntries(self):
        if self.grubRep in self.cache:
            for entry in self.cache[self.grubRep]:
                self.CustomEntriesList.addItem(entry)
            print("Loaded")
        else:
            if (self.grubRep / "custom.cfg").exists():
                customContent = (self.grubRep / "custom.cfg").lines()
                for line in customContent:
                    instruction = False
                    if "iso_boot" in line:
                        line = shlex.split(line)
                        permanent = True
                        name = line[1]
                        isoLocation = line[3].replace("}", "") # Virer les accolades de la fin (s'il y en a)
                        if len(line) == 6:
                            loopbackLocation = line[4][:-1] # Idem, mais on est sûr qu'il y en a
                        else:
                            loopbackLocation = None # Ne pas oublier d'instancier la variable
                        instruction = True
                    elif "amorce_iso" in line:
                        line = shlex.split(line)
                        permanent = False
                        isoLocation = line[1]
                        name = basename(isoLocation)
                        if len(line) == 4:
                            loopbackLocation = line[2]
                        else:
                            loopbackLocation = None
                        instruction = True
                    if instruction:
                        mountpoint = line[-1][1:]
                        entry = CustomEntry(self.CustomEntriesList, name, isoLocation, permanent, loopbackLocation, mountpoint)
                if self.CustomEntriesList.count() == 0:
                    self.addNewItem()
                self.addEntriesToCache()
            else:
                self.addNewItem()
                self.addEntriesToCache()
        self.CustomEntriesList.setCurrentRow(0)
        
        
    
    def addNewItem(self):
        permanent = True
        name = "<New>"
        entry = CustomEntry(self.CustomEntriesList, name, permanent=permanent)
        self.CustomEntriesList.setCurrentItem(entry)
        self.addEntriesToCache()
    
    def removeCurrentItem(self):
        current = self.CustomEntriesList.currentRow()
        item = self.CustomEntriesList.takeItem(current)
        self.cache[self.grubRep].remove(item)
    
    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def setGrubRep(self, grubRep, prevGrubRep):
        self.grubRep = path.Path(grubRep.text())
        for i in range(self.CustomEntriesList.count()):
            self.CustomEntriesList.takeItem(0)
        self.getCustomEntries()
    
    @pyqtSlot(str)
    def setIsoLocation(self, isoLocation):
        mountpoint = find_mount(isoLocation)
        isoLocation = isoLocation.replace(mountpoint, "", 1)
        current = self.CustomEntriesList.currentItem()
        current.setIsoLocation(isoLocation)
        current.setMountPoint(mountpoint)
    
    @pyqtSlot(str)
    def setLoopbackContent(self, loopbackContent):
        current = self.CustomEntriesList.currentItem()
        current.setLoopbackContent(loopbackContent)
    
    @pyqtSlot(Qt.CheckState)
    def setPermanent(self, permanent):
        print("changed permanent :", end=" ")
        current = self.CustomEntriesList.currentItem()
        if permanent == Qt.Checked:
            current.setPermanent(True)
            print(True)
        else:
            for item in [self.CustomEntriesList.item(i) for i in range(self.CustomEntriesList.count())]:
                item.setPermanent(True)
            current.setPermanent(False)
            print(False)
    
    def addEntriesToCache(self):
        items = [self.CustomEntriesList.item(i) for i in range(self.CustomEntriesList.count())]
        self.cache[self.grubRep] = items
    
    def emitSignal(self, current, previous):
        if current == None: pass
        else:
            print(current.text())
            self.currentItemChanged.emit(current)
    
    def getCurrent(self):
        return self.CustomEntriesList.currentItem()

    def getCache(self):
        return self.cache

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    win = CustomEditor("/boot/grub")
    win.setWindowTitle("Custom Editor")
    win.show()
    
    app.exec_()
