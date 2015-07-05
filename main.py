#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# Modules standards
import sys
import os
import subprocess
import argparse

# Modules tiers
from path import path
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (QMainWindow, QApplication,
                             qApp, QAction, QPushButton,
                             QHBoxLayout, QVBoxLayout,
                             QWidget, QSplitter, QMessageBox)

# Modules persos
from grub import GrubList
from editor import Editor
from options import Options
from custom_editor import CustomEditor, CustomEntry

class MainWindow(QMainWindow):
    """Fenêtre principale du programme"""
    # Fichiers
    grubFonctionsFile = path("fonctions_iso.cfg")
    # Insctructions
    customIncipit = "source ${prefix}/greffons/fonctions_iso.cfg\n"
    grubConf = ("if [ -f  ${config_directory}/custom.cfg ]; then\n"
                "  source ${config_directory}/custom.cfg\n"
                'elif [ -z "${config_directory}" -a -f  $prefix/custom.cfg ]; then\n'
                "  source $prefix/custom.cfg;\n"
                "fi\n")
    
    def __init__(self, grubDir="/boot/grub"):
        QMainWindow.__init__(self)
        # Variables
        self.grubDir = path(grubDir)
        
        # Création des éléments
        # Left
        self.customEditor = CustomEditor()
        self.options = Options(self)
        # Right
        self.editor = Editor(self)
        valid = QPushButton("Valider")
        valid.clicked.connect(self.valid)
        cancel = QPushButton("Quitter")
        cancel.clicked.connect(qApp.quit)
        # Top
        menubar = self.menuBar()
        
        # Création des Layout
        # Boutons
        buttons = QHBoxLayout()
        buttons.addWidget(valid)
        buttons.addWidget(cancel)
        # Left
        left = QVBoxLayout()
        left.addWidget(self.customEditor)
        left.addWidget(self.options)
        leftW = QWidget()
        leftW.setLayout(left)
        # Right
        right = QVBoxLayout()
        right.addWidget(self.editor)
        right.addLayout(buttons)
        rightW = QWidget()
        rightW.setLayout(right)
        # Window
        window = QSplitter()
        window.addWidget(leftW)
        window.addWidget(rightW)
        self.setCentralWidget(window)
        
        # Création des menus
        # Fichier
        quit = QAction("Quitter", self)
        quit.setShortcut('Ctrl+Q')
        quit.triggered.connect(qApp.quit)
        openISO = QAction("Sélectionner une ISO", self)
        openISO.triggered.connect(self.editor.open_iso)
        openLoop = QAction("Ouvrir un fichier loopback", self)
        openLoop.triggered.connect(self.editor.open_loopback)
        fileMenu = menubar.addMenu("Fichier")
        fileMenu.addAction(openISO)
        fileMenu.addAction(openLoop)
        fileMenu.addAction(quit)
        # Loopback
        genLoop = QAction("Générer le fichier loopback", self)
        genLoop.triggered.connect(self.editor.gen_loopback)
        setFrench = QAction('Ajouter les traductions françaises', self)
        setFrench.triggered.connect(self.editor.addFrenchTranslations)
        loopMenu = menubar.addMenu("Loopback")
        loopMenu.addAction(genLoop)
        loopMenu.addAction(setFrench)
        
        # Signaux
        self.customEditor.currentItemChanged.connect(self.updateDisplay)
        self.editor.iso_location.textChanged.connect(self.customEditor.setIsoLocation)
        self.editor.textChanged.connect(self.customEditor.setLoopbackContent)
        self.options.permanentCB.stateChanged.connect(self.customEditor.setPermanent)
            
        # Initialisation de l'interface
        self.setWindowTitle("GrubEnhancer")
        self.loadGrubDir()
        self.updateDisplay(self.customEditor.getCurrent())
        
    @pyqtSlot(CustomEntry)
    def updateDisplay(self, entry):
        # Obtention des paramètres de l'entrée
        mountpoint = entry.getMountPoint()
        isoLocation = path(mountpoint) / entry.getIsoLocation()[1:]
        loopbackContent = entry.getLoopbackContent()
        permanent = entry.getPermanent()
        enabled = entry.getEnabled()
        # Mise à jour de l'interface
        self.editor.loopback_edit.setPlainText(loopbackContent)
        self.editor.iso_location.setText(isoLocation)
        if permanent:
            self.options.permanentCB.setCheckState(Qt.Checked)
        else:
            self.options.permanentCB.setCheckState(Qt.Unchecked)
        if isoLocation.exists():
            entry.setEnabled(True)
            self.editor.setEnabled(True)
            self.options.setEnabled(True)
        else:
            entry.setEnabled(False)
            self.editor.setEnabled(False)
            self.options.setEnabled(False)
    
    def valid(self):
        """Lance la procédure de mise à jour de Grub,
        après avoir vérifié que tous les paramètres
        étaient bien donnés"""
        cache = self.customEditor.getCache()
        entries = cache[self.grubDir]
        # Mise à jour de la config de GRUB
        grub_config_file = self.grubDir / "grub.cfg"
        if self.grubConf not in grub_config_file.text():
            grub_config_file.write_text("### BEGIN GrubEnhancer Config ###\n" + self.grubConf + "### END GrubEnhancer Config ###\n", append=True)
        # Écriture des fonctions GRUB
        greffons = self.grubDir / "greffons"
        if not greffons.isdir():
            greffons.mkdir()
        fonctionsFile = greffons / "fonctions_iso.cfg"
        self.grubFonctionsFile.copy(fonctionsFile)
        # Création des Loopback et du Custom
        custom = self.grubDir / "custom.cfg"
        custom_content = [self.customIncipit]
        for entry in entries:
            # Récupération des paramètres
            name = entry.text()
            iso_location = entry.getIsoLocation()
            print(iso_location)
            loopback_content = entry.getLoopbackContent()
            loopback_location = iso_location.replace('.iso', '.loopback.cfg')
            mountpoint = entry.getMountPoint()
            permanent = entry.getPermanent()
            # Création du Loopback
            print(iso_location, loopback_location, mountpoint, sep=" : ")
            temporary = False
            if loopback_content:
                full_loopback_location = path(mountpoint) / loopback_location[1:] # On vire toujours le premier /
                full_loopback_location.write_text(loopback_content)
            # Création d'une ligne du Custom
            if permanent:
                if loopback_content:
                    custom_line = '\tsubmenu "' + name + '" {iso_boot "' + iso_location + '" "' + loopback_location + '"} #' + mountpoint + '\n'
                else:
                    custom_line = '\tsubmenu "' + name + '" {iso_boot "' + iso_location + '"} #' + mountpoint + '\n'
            else:
                if loopback_content:
                    custom_line = 'amorce_iso "{}" "{}" #{}\n'.format(iso, loopback, mountpoint)
                else:
                    custom_line = 'amorce_iso "{}" #{}\n'.format(iso, mountpoint)
                temporary = True
            custom_content.append(custom_line)
        # Création du Custom
        custom.write_lines(custom_content)
        # Affichage d'un message de confirmation
        msg = "Vos modifications ont bien été prises en compte."
        info = QMessageBox(self)
        info.setWindowTitle("GrubEnhancer")
        info.setText(msg)
        info.exec_()
    
    def loadGrubDir(self):
        
        self.customEditor.setGrubRep(self.grubDir)
        
        forbiddenFilesystem = ("btrfs", "cpiofs", "newc","odc",
                               "romfs", "squash4", "tarfs", "zfs")
        forbiddenDeviceName = ("/dev/mapper", "/dev/dm", "/dev/md")
        
        filesystem = subprocess.check_output(["grub-probe", "--target=fs", self.grubDir]).decode().split()[0]
        disque = subprocess.check_output(["grub-probe", "--target=disk", self.grubDir]).decode().split()[0]
        
        if filesystem in forbiddenFilesystem or disque.startswith(forbiddenDeviceName):
            self.options.setEnabled(False)
        else:
            self.options.setEnabled(True)

if __name__ == "__main__":
    
    if os.geteuid():
        print("Ce programme nécessite les droits administrateurs")
        sys.exit(1)
    else:
        app = QApplication(sys.argv)
        parser = argparse.ArgumentParser()
        parser.add_argument('-d', '--directory', default="/boot/grub", help="Le répertoire GRUB à utiliser")
        
        args = parser.parse_args()
        grubDir = args.directory
        
        if not (path(grubDir) / "grub.cfg").exists():
            choices = GrubList(text="{} ne semble pas être un répertoire GRUB.\nVeuillez en choisir un autre.".format(args.directory), allowNone=False)
            choices.setWindowTitle("Liste des répertoires GRUB")
            grubDir = choices.selectGrubRep()
        
        window = MainWindow(grubDir=grubDir)
        
        window.show()
        sys.exit(app.exec_())
