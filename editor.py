#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import tempfile
import subprocess
import path
from os.path import expanduser, join, exists
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import (QFrame, QApplication,
                             QLineEdit, QPushButton,
                             QPlainTextEdit,QHBoxLayout,
                             QVBoxLayout, QLabel,
                             QFileDialog, QMessageBox)

def find_mount(location):
    location = path.Path(location)
    if location.parent.ismount() or location.parent == "/":
        return location.parent
    else:
        return find_mount(location.parent)

class Editor(QFrame):
    
    textChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        
        # Création des éléments
        # Top
        self.iso_location = QLineEdit()
        self.iso_location.textChanged.connect(self.updateWarning)
        iso_choose = QPushButton("ISO")
        iso_choose.clicked.connect(self.open_iso)
        # Middle
        self.isoWarning = QLabel()
        self.isoWarning.setAlignment(Qt.AlignHCenter)
        label = QLabel("Fichier Loopback")
        label.setAlignment(Qt.AlignHCenter)
        self.loopback_edit = QPlainTextEdit()
        self.loopback_edit.textChanged.connect(self.emitChangedText)
        # Bottom
        loopback_choose = QPushButton("Ouvrir")
        loopback_gen = QPushButton("Générer")
        loopback_choose.clicked.connect(self.open_loopback)
        loopback_gen.clicked.connect(self.gen_loopback)
        
        
        # Création des Layouts
        # Top
        topbox = QHBoxLayout()
        topbox.addWidget(self.iso_location)
        topbox.addWidget(iso_choose)
        # Bottom
        botbox = QHBoxLayout()
        botbox.addWidget(loopback_choose)
        botbox.addWidget(loopback_gen)
        # Vertical
        vbox = QVBoxLayout()
        vbox.addLayout(topbox)
        vbox.addWidget(self.isoWarning)
        vbox.addWidget(label)
        vbox.addWidget(self.loopback_edit)
        vbox.addLayout(botbox)
        
        # Affichage de l'interface
        self.setLayout(vbox)
    
    @pyqtSlot()
    def open_iso(self):
        fichier = QFileDialog.getOpenFileName(self,
                                    "Sélectionner une image ISO",
                                    expanduser('~'),
                                    "Image Iso (*.iso)")[0]
        self.iso_location.setText(fichier)
    
    @pyqtSlot()
    def open_loopback(self):
        fichier = QFileDialog.getOpenFileName(self,
                                              "Sélectionner un fichier Loopback",
                                              expanduser('~'))[0]
        if fichier:
            content = open(fichier, 'r').read()
            self.loopback_edit.setPlainText(content)
    
    @pyqtSlot()
    def gen_loopback(self):
        if self.iso_location.text() == "":
            msg = "Il faut d'abord sélectionner une ISO avant de pouvoir générer un fichier loopback à partir de celle-ci !"
            QMessageBox.warning(self, "ISO non spécifiée", msg)
        else:
            with tempfile.TemporaryDirectory() as mountpoint:
                mount = subprocess.call(["mount",
                                        self.iso_location.text(),
                                        mountpoint])
                if mount:
                    msg = ("Il n'a pas été possible de monter l'ISO.\n"
                            "Une erreur a été rencontré pendant l'éxécution de la commande «mount».\n"
                            "Consultez la console pour plus de détails.")
                    QMessageBox.critical(self, "Impossible de monter l'ISO", msg)
                else:
                    fichier = join(mountpoint, "boot/grub/loopback.cfg")
                    if exists(fichier):
                        content = open(fichier, 'r').read()
                        self.loopback_edit.setPlainText(content)
                    else:
                        fichier = join(mountpoint, "boot/grub/grub.cfg")
                        if exists(fichier):
                            content = open(fichier, 'r').readlines()
                            for i in range(len(content)): 
                                if "linux" in content[i]:
                                    content[i].replace("\n", " iso-scan/filename=${iso_path}\n")
                            content = "".join(content)
                            self.loopback_edit.setPlainText(content)
                        else:
                            msg = ("L'iso sélectionnée ne contient pas de fichier loopback.\n"
                                   "Il n'est donc pas possible d'en générer un, il faut le créer manuellement.")
                            QMessageBox.information(self, "ISO non valable", msg)
                    
                    # Nécessaire de démonter l'ISO
                    subprocess.call(["umount", mountpoint])
    
    @pyqtSlot()
    def addFrenchTranslations(self):
        content = self.loopback_edit.toPlainText()
        content = content.split('\n')
        for i in range(len(content)):
            if "linux" in content[i]:
                content[i] += ' locale=fr_FR bootkbd=fr console-setup/layoutcode=fr console-setup/variantcode=oss'
        content = '\n'.join(content)
        self.loopback_edit.setPlainText(content)
    
    def getIsoLocation(self):
        return self.iso_location.text()
    
    def getLoopbackContent(self):
        return self.loopback_edit.toPlainText()
    
    @pyqtSlot()
    def updateWarning(self):
        isoPath = self.iso_location.text()
        isoPath = isoPath.replace(find_mount(isoPath), "", 1)
        if " " in isoPath:
            self.isoWarning.setText("<font color=#FF0000>Le chemin menant à l'ISO ne peut pas contenir d'espaces !</font>")
        else:
            self.isoWarning.setText("")
            self.isoWarning.setToolTip("")
    
    @pyqtSlot()
    def emitChangedText(self):
        self.textChanged.emit(self.loopback_edit.toPlainText())
    
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    win = Editor()
    win.setWindowTitle("Éditeur")
    win.show()
    
    app.exec_()
