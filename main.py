from PyQt6 import QtGui
from PyQt6.QtCore import QTranslator
from PyQt6.QtWidgets import QApplication
import sys

from Controllers.MainController import MainController


class Main:
    def __init__(self):
        # Window Icon
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Images/AppIcon/poland-map.png"), QtGui.QIcon.Mode.Normal,
                       QtGui.QIcon.State.Off)
        app.setWindowIcon(icon)

        # Translations
        plQtGuiPath = "Translations/PL/qtbase_pl.qm"

        if translator.load(plQtGuiPath):
            app.installTranslator(translator)

        # Controllers
        self.mainController = MainController()

        # Connections


translator = QTranslator()
app = QApplication(sys.argv)
window = Main()
sys.exit(app.exec())
