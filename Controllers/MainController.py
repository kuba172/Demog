import os

import pandas as pd
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QPointF, QDate
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QGraphicsScene, QGraphicsPolygonItem, QCompleter, \
    QMessageBox
from reportlab.pdfgen import canvas

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
                self.generatePdf(filePath)
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
        self.window_locations_list_ui.listWidget_Locatons_List.itemClicked.connect(self.handleSelectionChange)

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

    def handleSelectionChange(self):
        self.window_locations_list_ui.pushButton_Delete.setEnabled(True)

    def generatePdf(self, filePath):
        try:
            if filePath:
                pdf_canvas = canvas.Canvas(filePath)

                self.addTitlePage(pdf_canvas)
                self.addTableOfContents(pdf_canvas)
                self.addSummary(pdf_canvas)
                self.addIntroduction(pdf_canvas)
                self.addMethodology(pdf_canvas)
                self.addLocationDescription(pdf_canvas)
                self.addAnnualAnalysis(pdf_canvas)
                self.addResultsAndConclusions(pdf_canvas)
                self.addRecommendations(pdf_canvas)
                self.addClientSpecificContent(pdf_canvas)
                self.addSummaryReport(pdf_canvas)
                self.addReferences(pdf_canvas)
                self.addAttachments(pdf_canvas)

                pdf_canvas.save()
                self.statusConfirmation(filePath)

        except Exception as e:
            print(e)

    def addTitlePage(self, pdf_canvas):
        pdf_canvas.drawString(100, 750, "Raport z badania atrakcyjności biznesowej")
        pdf_canvas.drawString(100, 730, f"Kompleksowa analiza []")

    def addTableOfContents(self, pdf_canvas):
        pdf_canvas.showPage()
        pdf_canvas.drawString(100, 750, "Spis treści")

    def addSummary(self, pdf_canvas):
        pdf_canvas.showPage()
        pdf_canvas.drawString(100, 750, "Streszczenie")

    def addIntroduction(self, pdf_canvas):
        pdf_canvas.showPage()
        pdf_canvas.drawString(100, 750, "Wprowadzenie")

    def addMethodology(self, pdf_canvas):
        pdf_canvas.showPage()
        pdf_canvas.drawString(100, 750, "Metodologia")

    def addLocationDescription(self, pdf_canvas):
        pdf_canvas.showPage()
        pdf_canvas.drawString(100, 750, "Opis wybranej lokalizacji")

    def addAnnualAnalysis(self, pdf_canvas):
        pdf_canvas.showPage()
        pdf_canvas.drawString(100, 750, "Analiza roczna")

    def addResultsAndConclusions(self, pdf_canvas):
        pdf_canvas.showPage()
        pdf_canvas.drawString(100, 750, "Wyniki i wnioski")

    def addRecommendations(self, pdf_canvas):
        pdf_canvas.showPage()
        pdf_canvas.drawString(100, 750, "Zalecenia")

    def addClientSpecificContent(self, pdf_canvas):
        pdf_canvas.showPage()
        pdf_canvas.drawString(100, 750, "Dodatkowa treść specyficzna dla klienta")

    def addSummaryReport(self, pdf_canvas):
        pdf_canvas.showPage()
        pdf_canvas.drawString(100, 750, "Podsumowanie")

    def addReferences(self, pdf_canvas):
        pdf_canvas.showPage()
        pdf_canvas.drawString(100, 750, "Referencje")

    def addAttachments(self, pdf_canvas):
        pdf_canvas.showPage()
        pdf_canvas.drawString(100, 750, "Załączniki")

    def statusConfirmation(self, fileName):
        try:
            fileName = os.path.basename(fileName)
            message = "Raport '{}' został pomyślnie wygenerowany.".format(fileName)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setText(message)
            msg.setWindowTitle('DemoG')

            msg.setStandardButtons(QMessageBox.StandardButton.Close)
            msg.button(QMessageBox.StandardButton.Close).setText('Zamknij')

            reply = msg.exec()

            return reply == QMessageBox.StandardButton.Close
        except Exception as e:
            print(e)
