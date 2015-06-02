#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import subprocess
from os.path import expanduser
import path # Pour la fonction find
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtWidgets import (QFrame, QApplication,
                             QLabel, QListWidget,
                             QPushButton, QVBoxLayout,
                             QHBoxLayout, QAbstractItemView,
                             QFileDialog, QMessageBox,
                             QProgressDialog, QListWidgetItem)

#TODO Rajouter une progressbar plus précise ?
def find(rep, pattern):
    dir = path.Path(rep)
    result = list()
    result[:0] = dir.glob(pattern)
    for file in dir.dirs():
        if not (dir / file).islink():
            try : 
                result[:0] = find(dir / file, pattern)
            except (PermissionError, FileNotFoundError): pass
    return result

class Scanner(QThread):
    """Classe scannant le système de fichier pour trouver
    un pattern donné lors de l'instanciation"""
    
    value_changed = pyqtSignal(int)
    max_changed = pyqtSignal(int)
    found_rep = pyqtSignal(list)
    
    def __init__(self, rep, pattern):
        QThread.__init__(self)
        self.rep = path.Path(rep)
        self.pattern = pattern
    
    def run(self):
        result = self._scan(self.rep)
        result = [file.parent for file in result]
        self.found_rep.emit(result)
    
    def _scan(self, rep, value=0):
        self.max_changed.emit(len(rep.dirs()))
        self.value_changed.emit(value)
        rep = path.Path(rep)
        result = list()
        result[:0] = rep.glob(self.pattern)
        for file in rep.dirs():
            value += 1
            self.value_changed.emit(value)
            if not (rep / file).islink():
                try : 
                    result[:0] = find(rep / file, self.pattern)
                except (PermissionError, FileNotFoundError): pass
        return result

class GrubList(QFrame):
    """Classe représentant la liste des répertoires GRUB"""
    
    scanner = Scanner("/", "*/grub/grub.cfg")
    newCurrentItem = pyqtSignal(QListWidgetItem)
    
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        
        # Création des éléments
        # Label
        label = QLabel("Liste des répertoires GRUB")
        label.setAlignment(Qt.AlignHCenter)
        # List View
        self.grub_list = QListWidget()
        self.grub_list.setSelectionMode(QAbstractItemView.SingleSelection)
        # Buttons
        self.scanButton = QPushButton("Scanner")
        self.add = QPushButton("Ajouter")
        self.scanButton.clicked.connect(self.scan)
        self.add.clicked.connect(self.openSelectionDialog)
        self.scanButton.setToolTip("Cette opération peut être <b>très</b> longue !")
        
        # Création des Layouts
        # Horizontal
        hbox = QHBoxLayout()
        hbox.addWidget(self.scanButton)
        hbox.addWidget(self.add)
        # Vertical
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.grub_list)
        vbox.addLayout(hbox)
        
        # Affichage de l'interface
        self.setLayout(vbox)
        
        #Signals
        self.scanner.found_rep.connect(self.add_items)
        self.scanner.started.connect(self._scan_started)
        self.scanner.finished.connect(self._scan_finished)
        self.grub_list.currentItemChanged.connect(self.currentItemChanged)
        
        # Ajout de /boot/grub s'il existe
        if path.Path("/boot/grub/grub.cfg").exists():
            self.add_item("/boot/grub")
    
    def scan(self):
        warning = QMessageBox(self)
        msg =  ("Cette opération peut être très longue.\n"
                "Le logiciel va analyser toute votre arborescence de fichier "
                "pour chercher un éventuel dossier contenant la configuration de GRUB.")
        warning.setText(msg)
        warning.setInformativeText("Êtes-vous sûr de vouloir continuer ?")
        warning.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        warning.setDefaultButton(QMessageBox.No)
        warning.setWindowTitle("Attention")
        answer = warning.exec_()
        if answer == QMessageBox.Yes:
            self.scanner.start()
    
    def openSelectionDialog(self):
        dir = QFileDialog.getExistingDirectory(self,
                                               "Sélectionner un répertoire GRUB",
                                               expanduser('~'))
        if (path.Path(dir) / grub.cfg).exists():
            self.add_item(dir)
        else:
            error = QMessageBox(self)
            msg = "Ce répertoire n'est pas un répertoire GRUB valide !"
            error.setText(msg)
            error.setWindowTitle("Répertoire non valide")
            error.exec_()
    
    def getGrubRep(self):
        dir = self.grub_list.selectedItems()
        try:
            dir = dir[0].text()
        except IndexError:
            return False
        else:
            return dir
    
    @pyqtSlot(list)
    def add_items(self, items):
        self.grub_list.clear()
        for item in items:
            self.grub_list.addItem(item)
    
    @pyqtSlot(str)
    def add_item(self, dir):
        item = QListWidgetItem(dir, self.grub_list)
        self.grub_list.setCurrentItem(item)
    
    @pyqtSlot()
    def _scan_started(self):
        self.scanButton.setEnabled(False)
        self.add.setEnabled(False)
    
    @pyqtSlot()
    def _scan_finished(self):
        self.scanButton.setEnabled(True)
        self.add.setEnabled(True)
    
    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def currentItemChanged(self, current, previous):
        self.newCurrentItem.emit(current)

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    win = GrubList()
    win.setWindowTitle("Grub List")
    win.show()
    
    app.exec_()