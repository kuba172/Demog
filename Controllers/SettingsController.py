from PyQt6.QtWidgets import QMainWindow
from Views.Settings.settings_window import Ui_MainWindow_Settings


class SettingsController(QMainWindow, Ui_MainWindow_Settings):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def showSettingsWindow(self):
        self.show()
