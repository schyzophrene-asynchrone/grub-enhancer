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
        # Check Box
        self.permanentCB = QCheckBox("Permanent", self)
        self.permanentCB.stateChanged.connect(self._setPermanent)
        
        # Layouts
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.permanentCB)
        
        
        # Création des variables
        self.permanent = False
        
        # Affichage de l'interface
        self.setLayout(vbox)
        self.setFrameShape(6)
        
    def _setPermanent(self, state):
        if state == Qt.Checked:
            self.permanent = True
        else:
            self.permanent = False
        
    def getPermanent(self):
        """Renvoie l'état du boutton "permanent" """
        return self.permanent
    
    def disablePerm(self, state):
        self.permanentCB.setCheckState(state)
        self.permanentCB.setDisabled(True)
    
    def enablePerm(self, state):
        self.permanentCB.setEnabled(True)
        self.permanentCB.setCheckState(state)

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    win = Options()
    win.setWindowTitle("Options")
    win.show()
    
    sys.exit(app.exec_())