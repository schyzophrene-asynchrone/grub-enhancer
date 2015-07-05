#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import subprocess
from os.path import expanduser
import path # Pour la fonction find
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtWidgets import (QDialog, QApplication,
                             QLabel, QListWidget,
                             QPushButton, QVBoxLayout,
                             QHBoxLayout, QAbstractItemView,
                             QFileDialog, QMessageBox,
                             QListWidgetItem,
                             QDialogButtonBox, QProgressBar)

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
    dir_scanned = pyqtSignal(str)
    
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
        self.dir_scanned.emit(rep)
        result = list()
        result[:0] = rep.glob(self.pattern)
        for file in rep.dirs():
            value += 1
            self.value_changed.emit(value)
            self.dir_scanned.emit(rep / file)
            if not (rep / file).islink():
                try : 
                    result[:0] = find(rep / file, self.pattern)
                except (PermissionError, FileNotFoundError): pass
        return result

class GrubList(QDialog):
    """Classe représentant la liste des répertoires GRUB"""
    
    scanner = Scanner("/", "*/grub/grub.cfg")
    newCurrentItem = pyqtSignal(str)
    
    def __init__(self, parent=None, text="Choisissez un répertoire GRUB", allowNone=True):
        QDialog.__init__(self, parent)
        
        # Création des éléments
        # Labels
        label = QLabel(text)
        label.setAlignment(Qt.AlignHCenter)
        self.scanText = QLabel("No scan running")
        self.scanText.setAlignment(Qt.AlignHCenter)
        # List View
        self.grub_list = QListWidget()
        self.grub_list.setSelectionMode(QAbstractItemView.SingleSelection)
        # Buttons
        self.scanButton = QPushButton("Scanner")
        self.add = QPushButton("Ajouter")
        self.scanButton.clicked.connect(self.scan)
        self.add.clicked.connect(self.openSelectionDialog)
        self.scanButton.setToolTip("Cette opération peut être <b>très</b> longue !")
        if allowNone:
            self.buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
            self.buttonBox.rejected.connect(self.reject)
        else:
            self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        # Progressbar
        self.progressbar = QProgressBar()
        self.progressbar.setEnabled(False)
        
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
        vbox.addWidget(self.scanText)
        vbox.addWidget(self.progressbar)
        vbox.addWidget(self.buttonBox)
        
        # Affichage de l'interface
        self.setLayout(vbox)
        
        #Signals
        self.scanner.found_rep.connect(self.add_items)
        self.scanner.started.connect(self._scan_started)
        self.scanner.finished.connect(self._scan_finished)
        self.scanner.max_changed.connect(self.progressbar.setMaximum)
        self.scanner.value_changed.connect(self.progressbar.setValue)
        self.scanner.dir_scanned.connect(self._setScanText)
        
        # Ajout de /boot/grub s'il existe
        if path.Path("/boot/grub/grub.cfg").exists():
            self.add_item("/boot/grub")
    
    def selectGrubRep(self):
        self.setModal(True)
        result = self.exec_()
        if result == QDialog.Accepted:
            grubRep = self.getGrubRep()
            return grubRep
        else:
            return False
    
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
        if (path.Path(dir) / "grub.cfg").exists():
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
        self.grub_list.setCurrentRow(0)
    
    @pyqtSlot(str)
    def add_item(self, dir):
        item = QListWidgetItem(dir, self.grub_list)
        self.grub_list.setCurrentItem(item)
    
    @pyqtSlot()
    def _scan_started(self):
        self.progressbar.setEnabled(True)
        self.progressbar.setMinimum(0)
        self.scanButton.setEnabled(False)
        self.add.setEnabled(False)
    
    @pyqtSlot()
    def _scan_finished(self):
        self.progressbar.reset()
        self.progressbar.setEnabled(False)
        self.scanText.setText("No scan running")
        self.scanButton.setEnabled(True)
        self.add.setEnabled(True)
    
    @pyqtSlot(str)
    def _setScanText(self, text):
        self.scanText.setText("Scanning {}...".format(text))

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    win = GrubList()
    win.setWindowTitle("Grub List")
    grubDir = win.selectGrubRep()
    
    print(grubDir)