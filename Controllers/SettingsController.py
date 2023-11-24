from PyQt6.QtWidgets import QMainWindow
from qt_material import QtStyleTools
from PyQt6.QtCore import Qt, QDir
from Views.Settings.settings_window import Ui_MainWindow_Settings


class SettingsController(QMainWindow, Ui_MainWindow_Settings, QtStyleTools):

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.apply_stylesheet(self.app, 'Themes/dark_blue.xml')
        self.setWindowFlags(
            Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.setupUi(self)

        self.populateLanguage()
        self.populateThemes()

        # Connections
        self.comboBox_Theme.currentIndexChanged.connect(self.loadThem)

    def showSettingsWindow(self):
        self.show()

    def populateLanguage(self):
        languages = ["Polski", "English"]

        self.comboBox_Language.clear()
        self.comboBox_Language.addItems(languages)

    def populateThemes(self):
        themes_path = "Themes"
        themes = [entry.replace(".xml", "") for entry in QDir(themes_path).entryList(['*.xml'])]

        self.comboBox_Theme.clear()
        self.comboBox_Theme.addItems(themes)

    def loadThem(self):
        themes_path = "Themes/"
        extension = ".xml"
        them_name = self.comboBox_Theme.currentText()
        filename = themes_path + them_name + extension

        self.apply_stylesheet(self.app, filename)
