import json
import os

import pandas as pd
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QPointF, QDate, QFile
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QGraphicsScene, QGraphicsPolygonItem, QCompleter, \
    QMessageBox
from reportlab.pdfgen import canvas

import Models.data_storage_model
from Views.Main.main_window import Ui_MainWindow_Main
from Views.Main.about_app import Ui_Dialog_About_App
from Views.Main.locations_list import Ui_Dialog_Location_List

import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import Models_ML.model
from Models.data_storage_model import DataStorageModel

from plotnine import ggplot, aes, geom_bar, labs, geom_line

pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))


class MainController(QMainWindow, Ui_MainWindow_Main):
    SETTINGS_FILE = "settings.json"

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Report variable
        self.pageCreated = False

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
        self.comboBox_Date_From.currentIndexChanged.connect(self.selectedYear)
        self.action_Open.triggered.connect(self.runModel)

        self.show()

    def resultInManyFiles(self):
        if QFile.exists(MainController.SETTINGS_FILE):
            with open(MainController.SETTINGS_FILE, 'r') as file:
                settings_data = json.load(file)

        if 'report_in_many_files' in settings_data:
            report_in_many_files_value = settings_data['report_in_many_files']
            return report_in_many_files_value
        else:
            return False

    def getModelName(self):
        if QFile.exists(MainController.SETTINGS_FILE):
            with open(MainController.SETTINGS_FILE, 'r') as file:
                settings_data = json.load(file)

        if 'selected_model_name' in settings_data:
            report_in_many_files_value = settings_data['selected_model_name']
            return report_in_many_files_value
        else:
            return False

    def getFileNamePath(self):
        try:
            fileFilter = 'Plik PDF (*.pdf)'

            filePath, _ = QFileDialog.getSaveFileName(
                caption="Eksportuj plik",
                directory=os.path.expanduser("~/Desktop/raport.pdf"),
                filter=fileFilter,
                initialFilter='Plik PDF (*.pdf)')

            return filePath
        except Exception as e:
            print(e)

    def getDirectoryPath(self):
        try:
            folderPath = QFileDialog.getExistingDirectory(
                caption="Wybierz folder",
                directory=os.path.expanduser("~/Desktop"),
            )
            return folderPath
        except Exception as e:
            print(e)

    def checkDate(self):
        dateFrom = self.comboBox_Date_From.currentText()
        dataTo = self.comboBox_Date_To.currentText()

        if dateFrom and dataTo:
            return True
        else:
            return False

    def checkDistrict(self):
        if self.window_locations_list_ui.listWidget_Locatons_List.count() > 0:
            return True
        else:
            return False

    def runModel(self):
        districtList = [self.window_locations_list_ui.listWidget_Locatons_List.item(i).text() for i in
                        range(self.window_locations_list_ui.listWidget_Locatons_List.count())]

        dateFrom = self.comboBox_Date_From.currentText()
        dateTo = self.comboBox_Date_To.currentText()

        for district in districtList:
            Models_ML.model.start(str(district), int(dateFrom), int(dateTo))

    def updateReportField(self):
        self.section_pages = {}
        self.pageCreated = False

    def generateReport(self):
        try:
            filePath = None
            directoryPath = None

            resultCheckDistrict = self.checkDistrict()
            resultCheckDate = self.checkDate()
            districktKeys = None

            if resultCheckDistrict and resultCheckDate:

                if self.resultInManyFiles():
                    directoryPath = self.getDirectoryPath()
                    print("dir " + directoryPath)
                else:
                    filePath = self.getFileNamePath()
                    print("file " + filePath)

                self.runModel()
                districktKeys = DataStorageModel.get_all_keys()

                if filePath and filePath.endswith(".pdf"):

                    for key in districktKeys:
                        if key == districktKeys[len(districktKeys) - 1]:
                            success = self.generatePdf(filePath, key, save=True)

                        success = self.generatePdf(filePath, key, save=False)

                    self.statusConfirmation(filePath, success=success)
                    self.updateReportField()
                    return success
                elif directoryPath:
                    # todo each report in a different file
                    # success = self.generatePdf(filePath)
                    # self.statusConfirmation(filePath, success=success)
                    # return success
                    print("Not available yet")
                else:
                    return False

            elif resultCheckDistrict == False and resultCheckDate == False:
                print("The list of district is empty and dates not selected")
            elif resultCheckDistrict == False:
                print("The list of district is empty")
            elif resultCheckDate == False:
                print("Dates not selected")
            else:
                print("Something goes wrong")

        except Exception as e:
            print("Error occurred:", e)
            self.statusConfirmation(filePath, success=False)

    def populateDateFrom(self):
        self.comboBox_Date_From.clear()
        current_year = QDate.currentDate().year()
        for year in range(current_year, current_year + 6):
            self.comboBox_Date_From.addItem(str(year))

    def selectedYear(self):
        selected_year = self.comboBox_Date_From.currentText()
        self.populateDateTo(selected_year)

    def populateDateTo(self, selected_year=None):
        self.comboBox_Date_To.clear()
        if selected_year is None:
            current_year = QDate.currentDate().year()
        else:
            current_year = int(selected_year)
        for year in range(current_year, current_year + 6):
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

    def generatePdf(self, filePath, districtKey, save):
        self.section_pages = {}
        try:
            if filePath:
                if self.pageCreated == False:
                    self.pdf_canvas = canvas.Canvas(filePath)
                    self.pageCreated = True

                if QFile.exists(MainController.SETTINGS_FILE):
                    with open(MainController.SETTINGS_FILE, 'r') as file:
                        settings_data = json.load(file)

                self.addTitlePage(self.pdf_canvas, districtKey)

                if settings_data.get("table_of_contents", True):
                    self.addTableOfContents(self.pdf_canvas, districtKey)
                if settings_data.get("summary", True):
                    self.addSummary(self.pdf_canvas, districtKey)
                if settings_data.get("introduction", True):
                    self.addIntroduction(self.pdf_canvas, districtKey)
                if settings_data.get("methodology", True):
                    self.addMethodology(self.pdf_canvas, districtKey)
                if settings_data.get("description_of_the_location", True):
                    self.addLocationDescription(self.pdf_canvas, districtKey)
                if settings_data.get("annual_analysis", True):
                    self.addAnnualAnalysis(self.pdf_canvas, districtKey)
                if settings_data.get("results_and_conclusions", True):
                    self.addResultsAndConclusions(self.pdf_canvas, districtKey)
                if settings_data.get("recommendations", True):
                    self.addRecommendations(self.pdf_canvas, districtKey)
                if settings_data.get("additional_customer_specific_content", True):
                    self.addClientSpecificContent(self.pdf_canvas, districtKey)
                if settings_data.get("report_summary", True):
                    self.addSummaryReport(self.pdf_canvas, districtKey)
                if settings_data.get("references", True):
                    self.addReferences(self.pdf_canvas, districtKey)
                if settings_data.get("attachments", True):
                    self.addAttachments(self.pdf_canvas, districtKey)

                if save == True:
                    self.pdf_canvas.save()
                    DataStorageModel.clear()
                return True  # Indicates success

        except Exception as e:
            print(e)
            return False  # Indicates failure

    def start_new_page(self, pdf_canvas):
        pdf_canvas.showPage()
        self.current_page = pdf_canvas.getPageNumber()
        self.addPageNumber(pdf_canvas)

    def addPageNumber(self, pdf_canvas):
        page_num_text = f"Strona {self.current_page}"
        pdf_canvas.setFont("DejaVuSans", 9)
        pdf_canvas.drawString(inch, 0.75 * inch, page_num_text)

    def getCurrentPage(self):
        return self.current_page

    def addTitlePage(self, pdf_canvas, districtKey):

        # Set page size and margins
        page_width, page_height = letter
        margin = inch
        image_width = 2 * inch  # Adjust as needed
        image_height = 1 * inch  # Adjust as needed

        # Centered logo
        logo_path = os.path.join('images', 'AppIcon', 'icon-map-800-800.png')  # placeholder logo
        image_x = (page_width - image_width) / 2
        image_y = 600  # Adjust the Y-coordinate as needed
        pdf_canvas.drawImage(logo_path, image_x, image_y, width=image_width, height=image_height)

        # Report Title
        pdf_canvas.setFont("DejaVuSans-Bold", 18)
        title_x = page_width / 2
        title_y = 500  # Adjust as needed
        pdf_canvas.drawCentredString(title_x, title_y, "Raport z badania atrakcyjności biznesowej")
        pdf_canvas.setFont("DejaVuSans", 12)
        pdf_canvas.drawCentredString(title_x, title_y - 30, f"Kompleksowa analiza []")

        # Date of Report Generation
        pdf_canvas.setFont("DejaVuSans", 12)
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        date_x = page_width / 2
        date_y = title_y - 60  # Adjust as needed
        pdf_canvas.drawCentredString(date_x, date_y, f"Data wygenerowania raportu: {current_date}")

        # Selected Districts
        pdf_canvas.setFont("DejaVuSans", 12)
        list_widget_items = [self.window_locations_list_ui.listWidget_Locatons_List.item(i).text() for i in
                             range(self.window_locations_list_ui.listWidget_Locatons_List.count())]
        elements_x = page_width / 2
        elements_y = date_y - 30  # Adjust as needed
        pdf_canvas.drawCentredString(elements_x, elements_y, f"Wybrane powiaty: {', '.join(list_widget_items)}")

        # Selected dates
        pdf_canvas.setFont("DejaVuSans", 12)
        combo1_value = self.comboBox_Date_From.currentText()
        combo2_value = self.comboBox_Date_To.currentText()
        values_x = page_width / 2
        values_y = elements_y - 20  # Adjust as needed
        pdf_canvas.drawCentredString(values_x, values_y, f"Dane od roku {combo1_value}")
        pdf_canvas.drawCentredString(values_x, values_y - 20, f"Dane do roku: {combo2_value}")

        modelName = self.getModelName()
        pdf_canvas.drawCentredString(values_x, values_y - 40, f"Wybrany model: {modelName}")
        pdf_canvas.drawCentredString(values_x, values_y - 60, f"Aktulany  powiat: {districtKey}")

    def addTableOfContents(self, pdf_canvas, districtKey):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Spis treści'] = {'start': start_page, 'end': start_page}

        # ... Add content for the summary section ...
        pdf_canvas.drawString(100, 750, "Spis treści")

        # Update the end page for the section
        self.section_pages['Spis treści']['end'] = self.getCurrentPage()

    def addSummary(self, pdf_canvas, districtKey):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Streszczenie'] = {'start': start_page, 'end': start_page}

        # ... Add content for the summary section ...
        pdf_canvas.drawString(100, 750, "Streszczenie")

        # Update the end page for the section
        self.section_pages['Streszczenie']['end'] = self.getCurrentPage()

    def addIntroduction(self, pdf_canvas, districtKey):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Wprowadzenie'] = {'start': start_page, 'end': start_page}

        # ... Add content for the introduction section ...

        # Update the end page for the section
        self.section_pages['Wprowadzenie']['end'] = self.getCurrentPage()

    def addMethodology(self, pdf_canvas, districtKey):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Metodologia'] = {'start': start_page, 'end': start_page}

        # ... Add content for the methodology section ...

        # Update the end page for the section
        self.section_pages['Metodologia']['end'] = self.getCurrentPage()

    def addLocationDescription(self, pdf_canvas, districtKey):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Opis wybranej lokalizacji'] = {'start': start_page, 'end': start_page}

        # ... Add content for the location description section ...

        # Update the end page for the section
        self.section_pages['Opis wybranej lokalizacji']['end'] = self.getCurrentPage()

    def addAnnualAnalysis(self, pdf_canvas, districtKey):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Analiza roczna'] = {'start': start_page, 'end': start_page}

        # ... Add content for the annual analysis section ...

        # Update the end page for the section
        self.section_pages['Analiza roczna']['end'] = self.getCurrentPage()

    def addResultsAndConclusions(self, pdf_canvas, districtKey):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Wyniki i wnioski'] = {'start': start_page, 'end': start_page}

        # ... Add content for the results and conclusions section ...

        # Update the end page for the section
        self.section_pages['Wyniki i wnioski']['end'] = self.getCurrentPage()

    def addRecommendations(self, pdf_canvas, districtKey):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Zalecenia'] = {'start': start_page, 'end': start_page}

        # ... Add content for the recommendations section ...

        # Update the end page for the section
        self.section_pages['Zalecenia']['end'] = self.getCurrentPage()

    def addClientSpecificContent(self, pdf_canvas, districtKey):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Dodatkowa treść specyficzna dla klienta'] = {'start': start_page, 'end': start_page}

        # ... Add content for the client-specific content section ...

        # Update the end page for the section
        self.section_pages['Dodatkowa treść specyficzna dla klienta']['end'] = self.getCurrentPage()

    def addSummaryReport(self, pdf_canvas, districtKey):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Podsumowanie'] = {'start': start_page, 'end': start_page}

        # ... Add content for the summary report section ...

        # Update the end page for the section
        self.section_pages['Podsumowanie']['end'] = self.getCurrentPage()

    def addReferences(self, pdf_canvas, districtKey):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Referencje'] = {'start': start_page, 'end': start_page}

        # ... Add content for the references section ...

        # Update the end page for the section
        self.section_pages['Referencje']['end'] = self.getCurrentPage()

    def addAttachments(self, pdf_canvas, districtKey):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Załączniki'] = {'start': start_page, 'end': start_page}

        # ... Add content for the attachments section ...

        # Update the end page for the section
        self.section_pages['Załączniki']['end'] = self.getCurrentPage()

    def addPlot(self, dane, key):
        dane = Models.data_storage_model.DataStorageModel.get(key)
        ggplot(dane)

    def statusConfirmation(self, fileName, success=True):
        try:
            fileName = os.path.basename(fileName)
            msg = QMessageBox()
            msg.setWindowTitle('DemoG')

            if success:
                message = f"Raport '{fileName}' został pomyślnie wygenerowany."
                msg.setIcon(QMessageBox.Icon.Information)
            else:
                message = f"Błąd podczas generowania raportu '{fileName}'."
                msg.setIcon(QMessageBox.Icon.Warning)

            msg.setText(message)
            msg.setStandardButtons(QMessageBox.StandardButton.Close)
            msg.button(QMessageBox.StandardButton.Close).setText('Zamknij')

            reply = msg.exec()
            return reply == QMessageBox.StandardButton.Close

        except Exception as e:
            print(e)
