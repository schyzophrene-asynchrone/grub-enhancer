#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFrame, QApplication,
                             QLabel, QCheckBox, 
                             QRadioButton, QVBoxLayout)

class Options(QFrame):
    """Classe représentant les options de configuration de GRUB"""
    
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        
        # Création des éléments
        # Label
        label = QLabel("Options", self)
        label.setAlignment(Qt.AlignHCenter)
        # Radio Buttons
        restart_nowCB = QRadioButton("Redémarrer maintenant", self)
        restart_laterCB = QRadioButton("Redémarrer plus tard", self)
        restart_nowCB.toggled.connect(self._setRestart)
        restart_laterCB.toggle()
        # Check Box
        permanentCB = QCheckBox("Permanent", self)
        permanentCB.stateChanged.connect(self._setPermanent)
        
        # Layouts
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(restart_nowCB)
        vbox.addWidget(restart_laterCB)
        vbox.addWidget(permanentCB)
        
        
        # Création des variables
        self.permanent = False
        self.restart_now = False
        
        # Affichage de l'interface
        self.setLayout(vbox)
        self.setFrameShape(6)
        
    def _setPermanent(self, state):
        if state == Qt.Checked:
            self.permanent = True
        else:
            self.permanent = False
        
    def _setRestart(self, state):
        self.restart_now = state
        
    def getPermanent(self):
        """Renvoie l'état du boutton "permanent" """
        return self.permanent
    
    def getRestart(self):
        return self.restart_now

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    win = Options()
    win.setWindowTitle("Options")
    win.show()
    
    sys.exit(app.exec_())