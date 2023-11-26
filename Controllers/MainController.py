import os
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QPointF, QDate
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QGraphicsScene, QGraphicsPolygonItem
from Views.Main.main_window import Ui_MainWindow_Main


class MainController(QMainWindow, Ui_MainWindow_Main):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.showMaximized()

        self.populateDateFrom()
        self.populateDateTo()

        # Connections
        self.action_Exit.triggered.connect(self.close)
        self.pushButton_Generate_Report.clicked.connect(self.generateReport)
        self.action_Generate_Report.triggered.connect(self.generateReport)

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

    def populateDateFrom(self):
        self.comboBox_Date_From.clear()
        current_year = QDate.currentDate().year()
        for year in range(current_year, current_year + 6):
            self.comboBox_Date_From.addItem(str(year))

    def populateDateTo(self):
        self.comboBox_Date_To.clear()
        current_year = QDate.currentDate().year()
        for year in range(current_year + 1, current_year + 12):
            self.comboBox_Date_To.addItem(str(year))
