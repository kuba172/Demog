import os

import pandas as pd
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QPointF, QDate
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QGraphicsScene, QGraphicsPolygonItem, QCompleter
from Views.Main.main_window import Ui_MainWindow_Main
from Views.Main.about_app import Ui_Dialog_About_App
from Views.Main.locations_list import Ui_Dialog_Location_List


class MainController(QMainWindow, Ui_MainWindow_Main):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.showMaximized()

        self.populateDateFrom()
        self.populateDateTo()
        self.createLocationsList()
        self.addQCompleterAll()

        # Connections
        self.action_Exit.triggered.connect(self.close)
        self.pushButton_Generate_Report.clicked.connect(self.generateReport)
        self.action_Generate_Report.triggered.connect(self.generateReport)
        self.action_About_Program.triggered.connect(self.createAboutApp)
        self.pushButton_Add_Location.clicked.connect(self.addToLocationsList)
        self.lineEdit_Location.returnPressed.connect(self.addToLocationsList)

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

    def createAboutApp(self):
        self.window_about_app = QDialog()
        self.window_about_app_ui = Ui_Dialog_About_App()
        self.window_about_app_ui.setupUi(self.window_about_app)
        self.window_about_app.show()

    def createLocationsList(self):
        self.window_locations_list = QDialog()
        self.window_locations_list_ui = Ui_Dialog_Location_List()
        self.window_locations_list_ui.setupUi(self.window_locations_list)

        self.window_locations_list_ui.pushButton_Delete.clicked.connect(self.handleDeleteButtonClick)
        self.window_locations_list_ui.pushButton_Cancel.clicked.connect(self.window_locations_list.close)
        self.window_locations_list_ui.listWidget_Locatons_List.itemClicked.connect(self.test)

    def showLocationsList(self):
        self.window_locations_list.show()

    def addToLocationsList(self):
        try:
            item = self.lineEdit_Location.text().strip()
            self.label_Location_Error_Message.clear()

            df = pd.read_csv('Resources/locations-suggestion.tsv', delimiter='\t')
            if item in df['KOD POCZTOWY'].values:
                powiat_value = df.loc[df['KOD POCZTOWY'] == item, 'POWIAT'].iloc[0]
                if powiat_value not in [self.window_locations_list_ui.listWidget_Locatons_List.item(i).text()
                                        for i in range(self.window_locations_list_ui.listWidget_Locatons_List.count())]:
                    self.window_locations_list_ui.listWidget_Locatons_List.addItem(powiat_value)
                else:
                    self.label_Location_Error_Message.setText(f"Lokalizacja '{item}' jest już dodana")
            elif item in df['POWIAT'].values:
                if item not in [self.window_locations_list_ui.listWidget_Locatons_List.item(i).text()
                                for i in range(self.window_locations_list_ui.listWidget_Locatons_List.count())]:
                    self.window_locations_list_ui.listWidget_Locatons_List.addItem(item)
                else:
                    self.label_Location_Error_Message.setText(f"Lokalizacja '{item}' jest już dodana")
            else:
                if self.lineEdit_Location.text() != "":
                    self.label_Location_Error_Message.setText("Nieprawidłowa lokalizacja")

            self.lineEdit_Location.clear()

        except Exception as e:
            print(e)

    def addQCompleterAll(self):
        try:
            df = pd.read_csv("Resources/locations-suggestion.tsv", delimiter='\t')

            columns_to_suggest = ['KOD POCZTOWY', 'POWIAT']

            suggestions = set()
            for column in columns_to_suggest:
                unique_values = df[column].unique()
                suggestions.update(map(str, unique_values))

            completer = QCompleter(list(suggestions))
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)

            self.lineEdit_Location.setCompleter(completer)

        except Exception as e:
            print(e)

    def handleDeleteButtonClick(self):
        selected_items = self.window_locations_list_ui.listWidget_Locatons_List.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.window_locations_list_ui.listWidget_Locatons_List.takeItem(
                self.window_locations_list_ui.listWidget_Locatons_List.row(item))
            self.window_locations_list_ui.pushButton_Delete.setEnabled(False)

    def test(self):
        self.window_locations_list_ui.pushButton_Delete.setEnabled(True)
