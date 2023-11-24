from PyQt6.QtWidgets import QMainWindow
from qt_material import QtStyleTools

from Views.Settings.settings_window import Ui_MainWindow_Settings


class SettingsController(QMainWindow, Ui_MainWindow_Settings, QtStyleTools):

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.apply_stylesheet(self.app, 'dark_blue.xml')


        self.setupUi(self)


    def showSettingsWindow(self):
        self.show()
