import os
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QGraphicsScene, QGraphicsPolygonItem
from Views.Main.main_window import Ui_MainWindow_Main


class MainController(QMainWindow, Ui_MainWindow_Main):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Connections
        self.action_Exit.triggered.connect(self.close)
        self.pushButton_Generate_Report.clicked.connect(self.generateReport)
        self.showMaximized()
        self.show()

    def generateReport(self):
        try:
            fileFilter = ('Plik PDF (*.pdf)')

            filePath = QFileDialog.getSaveFileName(
                caption="Eksportuj plik",
                directory=os.path.expanduser("~/Desktop/raport.pdf"),
                filter=fileFilter,
                initialFilter='Plik PDF (*.pdf)')

            filePath = str(filePath[0])

            if filePath.endswith(".pdf"):
                # TODO add function to handle generate contents of report
                print(filePath)

        except Exception as e:
            print(e)
