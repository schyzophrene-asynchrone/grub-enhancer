#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import subprocess
from os.path import expanduser
import path # Pour la fonction find
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFrame, QApplication,
                             QLabel, QListWidget,
                             QPushButton, QVBoxLayout,
                             QHBoxLayout, QAbstractItemView,
                             QFileDialog, QMessageBox,
                             QProgressDialog)

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

class GrubList(QFrame):
    """Classe représentant la liste des répertoires GRUB"""
    
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
        scan = QPushButton("Scanner")
        add = QPushButton("Ajouter")
        scan.clicked.connect(self.scan)
        add.clicked.connect(self.add_item)
        scan.setToolTip("Cette opération peut être <b>très</b> longue !")
        
        # Création des Layouts
        # Horizontal
        hbox = QHBoxLayout()
        hbox.addWidget(scan)
        hbox.addWidget(add)
        # Vertical
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.grub_list)
        vbox.addLayout(hbox)
        
        # Affichage de l'interface
        self.setLayout(vbox)
    
    def scan(self):
        warning = QMessageBox(self)
        msg =  "Cette opération peut être très longue.\n"
        msg += "Le logiciel va analyser toute votre arborescence de fichier "
        msg += "pour chercher un éventuel dossier contenant la configuration de GRUB."
        warning.setText(msg)
        warning.setInformativeText("Êtes-vous sûr de vouloir continuer ?")
        warning.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        warning.setDefaultButton(QMessageBox.No)
        warning.setWindowTitle("Attention")
        answer = warning.exec_()
        if answer == QMessageBox.Yes:
            dirs = self._find("/", "*/grub/grub.cfg")
            self.grub_list.clear()
            for file in dirs:
                self.grub_list.addItem(file.parent)
    
    def _find(self, rep, pattern):
        dir = path.Path(rep)
        value = 0
        progress = QProgressDialog("Recherche...", "Stop", 0, len(dir.dirs()), self)
        progress.setWindowTitle("Recherche")
        progress.setValue(0)
        progress.open()
        result = list()
        result[:0] = dir.glob(pattern)
        for file in dir.dirs():
            value += 1
            progress.setValue(value)
            if progress.wasCanceled():
                return result
            if not (dir / file).islink():
                try : 
                    result[:0] = find(dir / file, pattern)
                except (PermissionError, FileNotFoundError): pass
        return result
    
    def add_item(self):
        dir = QFileDialog.getExistingDirectory(self,
                                               "Sélectionner un répertoire GRUB",
                                               expanduser('~'))
        self.grub_list.addItem(dir)
    
    def getGrubRep(self):
        dir = self.grub_list.selectedItems()
        try:
            dir = dir[0].text()
        except IndexError:
            return False
        else:
            return dir

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    win = GrubList()
    win.setWindowTitle("Grub List")
    win.show()
    
    app.exec_()
    print(win.getGrubRep())