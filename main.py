#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import editor
import grub
import options
import custom_editor
import path
import subprocess
from os.path import basename, exists, join
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (QMainWindow, QApplication,
                             QAction, qApp, QSplitter,
                             QHBoxLayout, QVBoxLayout,
                             QPushButton, QWidget, QLayout,
                             QMessageBox, QProgressBar,
                             QListWidgetItem)

def find_mount(location):
    location = path.Path(location)
    if location.parent.ismount() or location.parent == "/":
        return location.parent
    else:
        return find_mount(location.parent)

class MainWindow(QMainWindow):
    
    # Fichiers 
    custom_41 = path.Path("41_custom")
    grubFonctionsFile = path.Path("fonctions_iso.cfg")
    # Instructions
    incipit = "source ${prefix}/greffons/fonctions_iso.cfg\n"
    grubConf = ("if [ -f  \${config_directory}/custom.cfg ]; then\n"
                "source \${config_directory}/custom.cfg\n"
                'elif [ -z "\${config_directory}" -a -f  \$prefix/custom.cfg ]; then\n'
                "source \$prefix/custom.cfg;\n"
                "fi\n")
    
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        
        # Création des éléments
        # Left
        self.grubList = grub.GrubList(self)
        self.options = options.Options(self)
        # Middle
        self.editeur = editor.Editor(self)
        valid = QPushButton("Valider")
        valid.clicked.connect(self.valid)
        cancel = QPushButton("Quitter")
        cancel.clicked.connect(qApp.quit)
        # Right
        self.customEditeur = custom_editor.CustomEditor(self.grubList.getGrubRep())
        self.customEditeur.currentItemChanged.connect(self.updateDisplay)
        # Top
        menubar = self.menuBar()
        # Bottom
        statusbar = self.statusBar()
        self.progressBar = QProgressBar()
        statusbar.addWidget(self.progressBar)
        self.progressBar.hide()
        self.progressBar.setMaximum(5)
        self.progressBar.setValue(0)
        
        # Créations des Actions
        # Fichier
        quit = QAction("Quitter", self)
        quit.setShortcut('Ctrl+Q')
        quit.triggered.connect(qApp.quit)
        openISO = QAction("Sélectionner une ISO", self)
        openISO.triggered.connect(self.editeur.open_iso)
        openLoop = QAction("Ouvrir un fichier Loopback", self)
        openLoop.triggered.connect(self.editeur.open_loopback)
        fileMenu = menubar.addMenu("Fichier")
        fileMenu.addAction(openISO)
        fileMenu.addAction(openLoop)
        fileMenu.addAction(quit)
        # Grub
        openDir = QAction("Sélectionner un dossier", self)
        openDir.triggered.connect(self.grubList.add_item)
        scan = QAction("Scanner", self)
        scan.setStatusTip("Peut être long")
        scan.triggered.connect(self.grubList.scan)
        grubMenu = menubar.addMenu("Grub")
        grubMenu.addAction(openDir)
        grubMenu.addAction(scan)
        # Loopback
        genLoop = QAction("Générer le fichier Loopback", self)
        genLoop.triggered.connect(self.editeur.gen_loopback)
        setFrench = QAction("Ajouter les traductions françaises", self)
        setFrench.triggered.connect(self.editeur.addFrenchTranslations)
        loopMenu = menubar.addMenu("Loopback")
        loopMenu.addAction(genLoop)
        loopMenu.addAction(setFrench)
        # Aide
        about = QAction("À propos", self)
        about.triggered.connect(self.about)
        helpMenu = menubar.addMenu("Aide")
        helpMenu.addAction(about)
        
        # Création des Layouts
        # Buttons
        buttons = QHBoxLayout()
        buttons.addWidget(valid)
        buttons.addWidget(cancel)
        # Left
        left = QVBoxLayout()
        left.addWidget(self.grubList)
        left.addWidget(self.options)
        leftW = QWidget()
        leftW.setLayout(left)
        # Middle
        middle = QVBoxLayout()
        middle.addWidget(self.editeur)
        middle.addLayout(buttons)
        middleW = QWidget()
        middleW.setLayout(middle)
        # Right
        right = QVBoxLayout()
        right.addWidget(self.customEditeur)
        rightW = QWidget()
        rightW.setLayout(right)
        # Window
        window = QSplitter()
        window.addWidget(leftW)
        window.addWidget(middleW)
        window.addWidget(rightW)
        
        self.setCentralWidget(window)
        self.setWindowTitle("GrubEnhancer")
        self.updateDisplay(self.customEditeur.getCurrent())
        
        # Signals
        self.grubList.scanner.started.connect(self.progressBar.show)
        self.grubList.scanner.max_changed.connect(self.progressBar.setMaximum)
        self.grubList.scanner.value_changed.connect(self.progressBar.setValue)
        self.grubList.scanner.finished.connect(self.progressBar.hide)
        self.grubList.grub_list.currentItemChanged.connect(self.checkGrubFileSystem)
        self.grubList.grub_list.currentItemChanged.connect(self.customEditeur.setGrubRep)
        self.editeur.iso_location.textChanged.connect(self.customEditeur.setIsoLocation)
        self.editeur.textChanged.connect(self.customEditeur.setLoopbackContent)
        self.options.permanentCB.stateChanged.connect(self.customEditeur.setPermanent)
        
    def valid(self):
        """Lance la procédure de mise à jour de Grub,
        après avoir vérifié que tous les paramètres
        étaient bien donnés"""
        cache = self.customEditeur.getCache()
        for grubRep, entries in cache.items():
            grubRep = path.Path(grubRep)
            # Mise à jour de la config de GRUB
            grub_config_file = grubRep / "grub.cfg"
            if self.grubConf not in grub_config_file.text():
                grub_config_file.write_text("### BEGIN GrubEnhancer Config ###\n" + self.grubConf + "### END GrubEnhancer Config ###\n", append=True)
            # Écriture des fonctions GRUB
            greffons = grubRep / "greffons"
            if not greffons.isdir():
                greffons.mkdir()
            fonctionsFile = greffons / "fonctions_iso.cfg"
            self.grubFonctionsFile.copy(fonctionsFile)
            # Création des Loopback et du Custom
            custom = grubRep / "custom.cfg"
            custom_content = [self.incipit]
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
                if loopback_content:
                    full_loopback_location = path.Path(mountpoint) / loopback_location[1:] # On vire toujours le premier /
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
                    subprocess.call(['grub-editenv', grubRep + '/grubenv', 'set', 'amorceiso=true'])
                custom_content.append(custom_line)
            # Création du Custom
            custom.write_lines(custom_content)
        # Affichage d'un message de confirmation
        msg = "Vos modifications ont bien été prises en compte."
        info = QMessageBox(self)
        info.setWindowTitle("GrubEnhancer")
        info.setText(msg)
        info.exec_()
    
    def about(self):
        msg = ("Ce programme a été créé pour vous permettre de lancer une image iso sans avoir besoin de la graver.\n\n"
               "Le script lu par Grub a été créé par Arbiel.\n"
               "La fenêtre que vous avez sous les yeux a été codée par Laërte\n\n"
               "Ce programme nécessite que vous utilisiez Grub comme chargeur d'amorçage. "
               "Si ce n'est pas le cas, consultez la liste des paquets fournis par votre distribution pour l'installer. "
               "Sans Grub, ce programme n'est d'aucune utilité.")
        description = QMessageBox(self)
        description.setText("GrubEnhancer")
        description.setInformativeText(msg)
        description.exec_()
    
    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def checkGrubFileSystem(self, grub_dir, prev_grub_dir):
        grub_dir = grub_dir.text()
        filesystem = subprocess.check_output(["grub-probe", "--target=fs", grub_dir]).decode().split()[0]
        if filesystem in ("btrfs", "cpiofs", "newc","odc",
                          "romfs", "squash4", "tarfs", "zfs"):
            self.options.disablePerm(Qt.Checked)
        else:
            disque = subprocess.check_output(["grub-probe", "--target=disk", grub_dir]).decode().split()[0]
            if disque.startswith(("/dev/mapper", "/dev/dm", "/dev/md")):
                self.options.disablePerm(Qt.Checked)
            else:
                self.options.enablePerm()
    
    @pyqtSlot(custom_editor.CustomEntry)
    def updateDisplay(self, item):
        mountpoint = item.getMountPoint()
        isoLocation = path.Path(mountpoint) / item.getIsoLocation()[1:]
        loopbackContent = item.getLoopbackContent()
        permanent = item.getPermanent()
        enabled = item.getEnabled()
        self.editeur.loopback_edit.setPlainText(loopbackContent)
        self.editeur.iso_location.setText(isoLocation)
        if permanent:
            self.options.permanentCB.setCheckState(Qt.Checked)
        else:
            self.options.permanentCB.setCheckState(Qt.Unchecked)
        if exists(isoLocation):
            enabled = True
            item.setEnabled(True)
        else:
            enabled = False
            item.setEnabled(False)
        if not enabled:
            self.options.setDisabled(True)
            self.editeur.setDisabled(True)
        else:
            self.options.setEnabled(True)
            self.editeur.setEnabled(True)
    
    
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
