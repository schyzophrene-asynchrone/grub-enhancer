#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import tempfile
import subprocess
from os.path import expanduser, join
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFrame, QApplication,
                             QLineEdit, QPushButton,
                             QPlainTextEdit,QHBoxLayout,
                             QVBoxLayout, QLabel,
                             QFileDialog, QMessageBox)

class Editor(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        
        # Création des éléments
        # Top
        self.iso_location = QLineEdit()
        iso_choose = QPushButton("ISO")
        iso_choose.clicked.connect(self.open_iso)
        # Middle
        label = QLabel("Fichier Loopback")
        label.setAlignment(Qt.AlignHCenter)
        self.loopback_edit = QPlainTextEdit()
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
        vbox.addWidget(label)
        vbox.addWidget(self.loopback_edit)
        vbox.addLayout(botbox)
        
        # Affichage de l'interface
        self.setLayout(vbox)
    
    def open_iso(self):
        fichier = QFileDialog.getOpenFileName(self,
                                    "Sélectionner une image ISO",
                                    expanduser('~'),
                                    "Image Iso (*.iso)")[0]
        self.iso_location.setText(fichier)
    
    def open_loopback(self):
        fichier = QFileDialog.getOpenFileName(self,
                                              "Sélectionner un fichier Loopback",
                                              expanduser('~'))[0]
        if fichier:
            content = open(fichier, 'r').read()
            self.loopback_edit.setPlainText(content)
    
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
                    msg = "Il n'a pas été possible de monter l'ISO.\n"
                    msg += "Une erreur a été rencontré pendant l'éxécution de la commande «mount».\n"
                    msg += "Consultez la console pour plus de détails."
                    QMessageBox.critical(self, "Impossible de monter l'ISO", msg)
                else:
                    fichier = join(mountpoint, "boot/grub/loopback.cfg")
                    content = open(fichier, 'r').read()
                    self.loopback_edit.setPlainText(content)
                    
                    # Nécessaire de démonter l'ISO
                    subprocess.call(["umount", mountpoint])
    
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
    
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    win = Editor()
    win.setWindowTitle("Éditeur")
    win.show()
    
    app.exec_()
