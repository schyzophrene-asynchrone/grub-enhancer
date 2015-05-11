#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import editor
import grub
import options
import path
import subprocess
from os.path import basename
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QMainWindow, QApplication,
                             QAction, qApp, QSplitter,
                             QHBoxLayout, QVBoxLayout,
                             QPushButton, QWidget, QLayout,
                             QMessageBox, QProgressBar)

def find_mount(location):
    location = path.Path(location)
    if location.parent.ismount() or location.parent == "/":
        return location.parent
    else:
        return find_mount(location.parent)

class MainWindow(QMainWindow):
    
    custom_41 = path.Path("41_custom")
    grubFonctionsFile = path.Path("fonctions_iso.cfg")
    incipit = "source ${prefix}/greffons/fonctions_iso.cfg\n"
    
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        
        # Création des éléments
        # Left
        self.grubList = grub.GrubList(self)
        self.options = options.Options(self)
        # Right
        self.editeur = editor.Editor(self)
        valid = QPushButton("Valider")
        valid.clicked.connect(self.valid)
        cancel = QPushButton("Quitter")
        cancel.clicked.connect(qApp.quit)
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
        # Right
        right = QVBoxLayout()
        right.addWidget(self.editeur)
        right.addLayout(buttons)
        rightW = QWidget()
        rightW.setLayout(right)
        # Window
        window = QSplitter()
        window.addWidget(leftW)
        window.addWidget(rightW)
        
        self.setCentralWidget(window)
        self.setWindowTitle("GrubEnhancer")
        
        # Signals
        self.grubList.scanner.started.connect(self.progressBar.show)
        self.grubList.scanner.max_changed.connect(self.progressBar.setMaximum)
        self.grubList.scanner.value_changed.connect(self.progressBar.setValue)
        self.grubList.scanner.finished.connect(self.progressBar.hide)
        
    def valid(self):
        """Lance la procédure de mise à jour de Grub,
        après avoir vérifié que tous les paramètres
        étaient bien donnés"""
        if self.grubList.getGrubRep() and self.editeur.getIsoLocation():
            self.progressBar.show()
            self.progressBar.setMaximum(5)
            self.progressBar.setValue(0)
            success = self._checkGrubConfig()
            self.progressBar.setValue(1)
            success = self._updateGrub()
            self.progressBar.setValue(2)
            succes = self._writeFunction()
            self.progressBar.setValue(3)
            succes = self._writeLoopback()
            self.progressBar.setValue(4)
            succes = self._updateCustom()
            self.progressBar.setValue(5)
            msg = "La configuration de Grub a bien été mise à jour."
            if self.options.getRestart(): msg += "\nL'ordinateur va maintenant redémarrer."
            QMessageBox.information(self, "Mise à jour effectuée", msg)
            self._restart()
            self.progressBar.reset()
            self.progressBar.hide()
        else:
            msg = "Vous devez préciser au moins une ISO et un répertoire GRUB !"
            QMessageBox.critical(self, "Paramètres manquants", msg)
        
    def _checkGrubConfig(self, rep="/etc/grub.d/"):
        """Vérifie la présence du fichier «41_custom» dans le
        répertoire "/etc/grub.d". Le crée sinon."""
        grub_dir = path.Path(rep)
        files = grub_dir.files()
        if "41_custom" in files: return True
        else:
            custom = grub_dir / "41_custom"
            copy = self.custom_41.copy(custom)
            copy.chmod(0o755)
            return True
    
    def _updateGrub(self):
        """Met à jour la configuration de grub"""
        grub_dir = path.Path(self.grubList.getGrubRep())
        config_file = grub_dir / "grub.cfg"
        subprocess.call(["grub-mkconfig", "-o", config_file])
        return True
    
    def _writeFunction(self):
        """Écrit les fonctions nécessaires au démarrage
        sur iso dans le répertoire grub. Les fonctions sont
        lues à partir de «file»"""
        grub_dir = path.Path(self.grubList.getGrubRep())
        try:
            grub_dir.joinpath("greffons").mkdir()
        except OSError: pass # Le répertoire existe déjà
        self.grubFonctionsFile.copy(grub_dir / "greffons/fonctions_iso.cfg")
        return True
    
    def _writeLoopback(self):
        """Écrit le fichier loopback"""
        content = self.editeur.getLoopbackContent().strip()
        if content:
            loopback = path.Path(self.editeur.getIsoLocation().replace(".iso", ".loopback.cfg"))
            loopback.write_text(content)
        return True
    
    def _updateCustom(self):
        """Modifie le fichier contenant les entrées du menu"""
        grub_dir = path.Path(self.grubList.getGrubRep())
        custom = grub_dir / "custom.cfg"
        try: custom_content = custom.lines(encoding="utf-8")
        except OSError: custom_content = []

        # Rajout de l'incipit
        if self.incipit not in custom_content:
            custom_content[:0] = [self.incipit]

        # Suppression des instructions «amorce_iso»
        for line in custom_content:
            if "amorce_iso" in line:
                custom_content.remove(line)

        # Calcul des chemins depuis la racine de la partition
        iso = path.Path(self.editeur.getIsoLocation())
        mountpoint = find_mount(iso)
        iso = iso.replace(mountpoint, "", 1)
        if self.editeur.getLoopbackContent().strip():
            loopback = iso.replace(".iso", ".loopback.cfg")
        else:
            loopback = None

        # Obtention du nom de l'iso
        iso_name = basename(iso)
        
        # Obtention des variables
        perm = self.options.getPermanent()
        
        if perm:
            if loopback:
                config = '\tsubmenu "' + iso_name + '" {iso_boot "' + iso + '" "' + loopback + '"}\n'
            elif not loopback:
                config = '\tsubmenu "' + iso_name + '" {iso_boot "' + iso + '"}\n'
        else:
            if loopback:
                config = 'amorce_iso "{}" "{}"\n'.format(iso, loopback)
            elif not loopback:
                config = 'amorce_iso "{}"\n'.format(iso)
            subprocess.call(['grub-editenv', '/boot/grub/grubenv', 'set', 'amorceiso=true'])
        
        # Rajout si la ligne n'existait pas déjà
        if config not in custom_content: custom_content.append(config)
        custom_content = "".join(custom_content)
        custom.write_text(custom_content)
        
        return True
    
    def _restart(self):
        """Redémarre si voulu"""
        if self.options.getRestart():
            subprocess.call(["shutdown", "-r", "now"])
    
    def about(self):
        msg = "Ce programme a été créé pour vous permettre de lancer une image iso sans avoir besoin de la graver.\n\n"
        msg += "Le script lu par Grub a été créé par Arbiel.\n"
        msg += "La fenêtre que vous avez sous les yeux a été codée par Laërte\n\n"
        msg += "Ce programme nécessite que vous utilisiez Grub comme chargeur d'amorçage. "
        msg += "Si ce n'est pas le cas, consultez la liste des paquets fournis par votre distribution pour l'installer. "
        msg += "Sans Grub, ce programme n'est d'aucune utilité."
        description = QMessageBox(self)
        description.setText("GrubEnhancer")
        description.setInformativeText(msg)
        description.exec_()
    
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
