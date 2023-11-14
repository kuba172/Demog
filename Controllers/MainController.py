from PyQt6.QtWidgets import QMainWindow
from Views.Main.main_window import Ui_MainWindow_Main


class MainController(QMainWindow, Ui_MainWindow_Main):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.show()

