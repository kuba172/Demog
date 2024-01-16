from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QCompleter, QMessageBox, QLabel, QGraphicsScene, \
    QGraphicsView, QApplication, QVBoxLayout, QPushButton, QWidget, QSlider, QGraphicsPathItem, QGraphicsItem, QToolTip
from PyQt6.QtGui import QPolygonF, QPainterPath, QPen, QBrush, QColor, QCursor
from PyQt6.QtCore import Qt, QDate, QFile, QPointF
from Views.Main.main_window import Ui_MainWindow_Main
from Views.Main.about_app import Ui_Dialog_About_App
from Views.Main.locations_list import Ui_Dialog_Location_List
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from Models.data_storage_model import DataStorageModel
from plotnine import ggplot, aes, geom_bar, labs, geom_line
import Models.data_storage_model
import Models_ML.model_random_forest_regression
import Models_ML.model_linear_regression
import Models_ML.model_polynomial_regression
import pandas as pd
import numpy as np
import datetime
import json
import sys
import os
import io

# Fonts
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))


class MainController(QMainWindow, Ui_MainWindow_Main):
    SETTINGS_FILE = "settings.json"

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Report variable
        self.pageCreated = False

        self.pathCurrentFile = None

        self.showMaximized()

        # Map
        self.map_color_rgba = [255, 255, 255, 255]
        self.border_map_color_rgba = [0, 0, 0, 255]
        self.selection_color_rgba = [255, 0, 0, 255]
        self.hover_color_rgba = [0, 0, 255, 255]
        self.map_border_size = 1
        self.selection_border_size = 3

        self.populateDateFrom()
        self.populateDateTo()
        self.createLocationsList()
        self.addQCompleterAll()
        self.addLabelToStatusBar()

        # Connections
        self.action_Exit.triggered.connect(self.close)
        self.pushButton_Generate_Report.clicked.connect(self.generateReport)
        self.action_Generate_Report.triggered.connect(self.generateReport)
        self.action_About_Program.triggered.connect(self.createAboutApp)
        self.pushButton_Add_Location.clicked.connect(self.addToLocationsList)
        self.lineEdit_Location.returnPressed.connect(self.addToLocationsList)
        self.comboBox_Date_From.currentIndexChanged.connect(self.selectedYear)
        self.action_Save.triggered.connect(self.saveAction)
        self.action_Save_As_New.triggered.connect(self.saveProjectNew)
        self.action_Open.triggered.connect(self.openProjectFile)
        self.comboBox_Date_From.currentIndexChanged.connect(self.updateStatusBar)
        self.comboBox_Date_To.currentIndexChanged.connect(self.updateStatusBar)

        self.horizontalSlider_Map_Size.setRange(50, 400)
        self.horizontalSlider_Map_Size.setValue(150)
        self.horizontalSlider_Map_Size.valueChanged.connect(self.zoomMap)

        # self.draw_map_in_graphics_view()

        # Test
        # self.updateMapSettings([223, 75, 23, 255], [0, 0, 0, 255], [22, 0, 220, 255], [0, 0, 255, 255], 3, 3)

        self.show()

    def updateMapSettings(self, map_color_rgba, border_map_color_rgba, selection_color_rgba, hover_color_rgba,
                          map_border_size, selection_border_size):
        self.map_color_rgba = map_color_rgba
        self.border_map_color_rgba = border_map_color_rgba
        self.selection_color_rgba = selection_color_rgba
        self.hover_color_rgba = hover_color_rgba
        self.map_border_size = map_border_size
        self.selection_border_size = selection_border_size

        # self.graphicsView_Map.deleteLater()
        # self.graphicsView_Map = QGraphicsView()
        # self.frame.layout().addWidget(self.graphicsView_Map)

        self.draw_map_in_graphics_view()

        self.zoomMap(self.horizontalSlider_Map_Size.value())

    def deleteAllLocations(self):
        districtsList = [self.window_locations_list_ui.listWidget_Locatons_List.item(i).text() for i in
                         range(self.window_locations_list_ui.listWidget_Locatons_List.count())]

        self.window_locations_list_ui.listWidget_Locatons_List.clear()

        for district in districtsList:
            self.changeColorByName(district,
                                   QColor(self.map_color_rgba[0], self.map_color_rgba[1], self.map_color_rgba[2],
                                          self.map_color_rgba[3]))

        self.updateStatusBar()

    def loadSavedItemsOnMap(self):
        districtsList = [self.window_locations_list_ui.listWidget_Locatons_List.item(i).text() for i in
                         range(self.window_locations_list_ui.listWidget_Locatons_List.count())]

        for item in districtsList:
            self.changeColorByName(item, QColor(self.selection_color_rgba[0], self.selection_color_rgba[1],
                                                self.selection_color_rgba[2], self.selection_color_rgba[3]))

    def changeColorByName(self, name, color):
        for key in self.items_dict:
            if key.startswith(name):
                item = self.items_dict.get(key)
                if item is not None:
                    item.setBrush(QBrush(QColor(color)))

    def zoomMap(self, value):
        self.graphicsView_Map.resetTransform()
        self.graphicsView_Map.scale(value / 100, value / 100)
        self.graphicsView_Map.scale(1, -1)
        self.graphicsView_Map.rotate(250)

    def addLabelToStatusBar(self):
        # localization count
        self.localizationCount = QLabel("   Brak wybranych lokalizacji")
        self.statusBar.setStyleSheet("QStatusBar::item { border: none; }")
        self.statusBar.addWidget(self.localizationCount)

        # report generation time
        self.reportGenerationTime = QLabel("Brak szacunkowego czasu wygenerowania raportu   ")
        self.statusBar.addPermanentWidget(self.reportGenerationTime)

    def updateStatusBar(self):
        newValue = self.window_locations_list_ui.listWidget_Locatons_List.count()
        dateFrom = int(self.comboBox_Date_From.currentText()) if self.comboBox_Date_From.currentText().isdigit() else 0
        dateTo = int(self.comboBox_Date_To.currentText()) if self.comboBox_Date_To.currentText().isdigit() else 0

        yearDifference = dateTo - dateFrom + 1
        estimatedTime = 10

        if dateFrom and dateTo and newValue > 0:
            result = newValue * yearDifference * estimatedTime
            self.reportGenerationTime.setText(f"Szacunkowy czas generowania raportu: {result} sekund    ")
        else:
            self.reportGenerationTime.setText("Brak szacunkowego czasu wygenerowania raportu   ")

        if newValue > 0:
            self.localizationCount.setText(f"   Liczba wybranych lokalizacji: {newValue}")
        else:
            self.localizationCount.setText(f"   Brak wybranych lokalizacji")

    def openProjectFile(self):
        try:
            fileFilter = 'Plik DemoG (*.demog)'
            fileName = QFileDialog.getOpenFileName(
                caption="Wczytaj projekt",
                directory=os.path.expanduser("~/Desktop/"),
                filter=fileFilter,
                initialFilter="Plik DemoG (*.demog)"
            )

            if fileName[0]:

                with open(fileName[0], "r") as file:
                    data = json.load(file)

                dateFrom = data.get("dateFrom", "")
                dateTo = data.get("dateTo", "")

                if dateFrom in [self.comboBox_Date_From.itemText(i) for i in range(self.comboBox_Date_From.count())]:
                    index = self.comboBox_Date_From.findText(dateFrom)
                    self.comboBox_Date_From.setCurrentIndex(index)

                if dateTo in [self.comboBox_Date_To.itemText(i) for i in range(self.comboBox_Date_To.count())]:
                    index = self.comboBox_Date_To.findText(dateTo)
                    self.comboBox_Date_To.setCurrentIndex(index)

                districtsList = data.get("districtsList", [])

                self.window_locations_list_ui.listWidget_Locatons_List.clear()
                self.window_locations_list_ui.listWidget_Locatons_List.addItems(districtsList)

                self.setSavedFilePath(fileName[0])

                self.loadSavedItemsOnMap()
                self.updateStatusBar()

        except Exception as e:
            print(e)

    def setSavedFilePath(self, filePath):
        newWindowTitle = f"{filePath} - DemoG"
        self.setWindowTitle(newWindowTitle)
        self.pathCurrentFile = filePath

    def saveAction(self):
        try:
            path = self.pathCurrentFile
            if path:
                self.save(self.pathCurrentFile)
            else:
                self.saveProjectNew()
        except Exception as e:
            print(e)

    def saveProjectNew(self):
        try:
            fileFilter = 'Plik DemoG (*.demog);;Wszystkie pliki (*.*)'

            fileName = QFileDialog.getSaveFileName(
                caption="Zapisz nowy projekt",
                directory=os.path.expanduser("~/Desktop/" + "nowy.demog"),
                filter=fileFilter,
                initialFilter="Plik DemoG (*.demog)"
            )

            if fileName[0] and fileName[0].endswith(".demog"):
                self.save(fileName[0])
                print(fileName[0])
            elif fileName[0]:
                print("Not supported extension")

        except Exception as e:
            print(e)

    def save(self, filePath):
        dateFrom = self.comboBox_Date_From.currentText()
        dateTo = self.comboBox_Date_To.currentText()
        districtsList = [self.window_locations_list_ui.listWidget_Locatons_List.item(i).text() for i in
                         range(self.window_locations_list_ui.listWidget_Locatons_List.count())]
        dataDump = {}

        dataDump["dateFrom"] = dateFrom
        dataDump["dateTo"] = dateTo
        dataDump["districtsList"] = districtsList

        if filePath:
            with open(filePath, "w") as file:
                json.dump(dataDump, file)

            self.setSavedFilePath(filePath)

        print(dateFrom, dateTo, districtsList)
        print(dataDump)

    def resultInManyFiles(self):
        if QFile.exists(MainController.SETTINGS_FILE):
            with open(MainController.SETTINGS_FILE, 'r') as file:
                settings_data = json.load(file)

        if 'report_in_many_files' in settings_data:
            report_in_many_files_value = settings_data['report_in_many_files']
            return report_in_many_files_value
        else:
            return False

    def getModelIndex(self):
        if QFile.exists(MainController.SETTINGS_FILE):
            with open(MainController.SETTINGS_FILE, 'r') as file:
                settings_data = json.load(file)

        if 'selected_model_index' in settings_data:
            selected_model_index = settings_data['selected_model_index']
            return int(selected_model_index)
        else:
            return False

    def getModelName(self):
        if QFile.exists(MainController.SETTINGS_FILE):
            with open(MainController.SETTINGS_FILE, 'r') as file:
                settings_data = json.load(file)

        if 'selected_model_name' in settings_data:
            selected_model_name = settings_data['selected_model_name']
            return selected_model_name
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

    def checkTargetGroup(self):
        if self.comboBox_Target_Group.currentIndex() >= 0:
            return True
        else:
            return False

    def runModel(self):
        districtList = [self.window_locations_list_ui.listWidget_Locatons_List.item(i).text() for i in
                        range(self.window_locations_list_ui.listWidget_Locatons_List.count())]

        dateFrom = self.comboBox_Date_From.currentText()
        dateTo = self.comboBox_Date_To.currentText()
        modelIndex = self.getModelIndex()

        # 0 - random_forest_regression
        # 1 - polynomial_regression
        # 2 - linear_regression

        if modelIndex == 0:
            for district in districtList:
                Models_ML.model_random_forest_regression.start(str(district), int(dateFrom), int(dateTo))
        elif modelIndex == 1:
            for district in districtList:
                Models_ML.model_polynomial_regression.start(str(district), int(dateFrom), int(dateTo))
        elif modelIndex == 2:
            for district in districtList:
                Models_ML.model_linear_regression.start(str(district), int(dateFrom), int(dateTo))
        else:
            self.errorStatus("Błąd modelu ucznia maszynowego", critical=True)

    def updateReportField(self):
        self.section_pages = {}
        self.pageCreated = False

    def generateReport(self):
        try:
            filePath = None
            directoryPath = None

            resultCheckDistrict = self.checkDistrict()
            resultCheckDate = self.checkDate()
            resultCheckTargetGroup = self.checkTargetGroup()

            districktKeys = None
            extensionPDF = ".pdf"

            if resultCheckDistrict and resultCheckDate and resultCheckTargetGroup:

                if self.resultInManyFiles():
                    directoryPath = self.getDirectoryPath()
                else:
                    filePath = self.getFileNamePath()

                if filePath or directoryPath:
                    self.runModel()
                    districktKeys = DataStorageModel.get_all_keys()

                    targetGroupIndex = self.comboBox_Target_Group.currentIndex()
                else:
                    return False

                if filePath and filePath.endswith(".pdf"):

                    for key in districktKeys:
                        if key == districktKeys[len(districktKeys) - 1]:
                            success = self.generatePdf(filePath, key, resultInOneFile=True, save=True,
                                                       targetGroupIndex=targetGroupIndex)

                        success = self.generatePdf(filePath, key, resultInOneFile=True, save=False,
                                                   targetGroupIndex=targetGroupIndex)

                    self.statusConfirmation(filePath, success=success)
                    self.updateReportField()
                    return success
                elif directoryPath:
                    for key in districktKeys:
                        filePath = f"{directoryPath}/{key}{extensionPDF}"
                        success = self.generatePdf(filePath, key, resultInOneFile=False, save=True,
                                                   targetGroupIndex=targetGroupIndex)

                    self.statusConfirmation(filePath, success=success)
                    self.updateReportField()
                else:
                    return False
            elif resultCheckDistrict == False and resultCheckDate == False and resultCheckTargetGroup == False:
                self.errorStatus("Wybierz lokalizację, przedział czasowy oraz grupę docelową")
            elif resultCheckDistrict == False and resultCheckDate == False and resultCheckTargetGroup == True:
                self.errorStatus("Wybierz lokalizację oraz przedział czasowy")
            elif resultCheckDistrict == False and resultCheckDate == True and resultCheckTargetGroup == False:
                self.errorStatus("Wybierz lokalizację oraz grupę docelową")
            elif resultCheckDistrict == True and resultCheckDate == False and resultCheckTargetGroup == False:
                self.errorStatus("Wybierz przedział czasowy oraz grupę docelową")
            elif resultCheckDistrict == False:
                self.errorStatus("Wybierz lokalizację")
            elif resultCheckDate == False:
                self.errorStatus("Wybierz przedział czasowy")
            elif resultCheckTargetGroup == False:
                self.errorStatus("Wybierz grupę docelową")
            else:
                self.errorStatus("Coś poszło nie tak", critical=True)

            return False

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
        self.window_locations_list_ui.pushButton_Delete_All.clicked.connect(self.deleteAllLocations)

    def showLocationsList(self):
        self.window_locations_list.show()

    def addToLocationsList(self):
        try:
            item = self.lineEdit_Location.text().strip()
            self.label_Location_Error_Message.clear()

            df = pd.read_csv('Resources/locations-suggestion.csv', delimiter=';')
            if item in df['KOD POCZTOWY'].values:
                powiat_value = df.loc[df['KOD POCZTOWY'] == item, 'POWIAT'].iloc[0]
                if powiat_value not in [self.window_locations_list_ui.listWidget_Locatons_List.item(i).text()
                                        for i in range(self.window_locations_list_ui.listWidget_Locatons_List.count())]:
                    self.window_locations_list_ui.listWidget_Locatons_List.addItem(powiat_value)
                    self.changeColorByName(item, QColor(self.selection_color_rgba[0], self.selection_color_rgba[1],
                                                        self.selection_color_rgba[2], self.selection_color_rgba[3]))
                else:
                    self.label_Location_Error_Message.setText(f"Lokalizacja '{item}' jest już dodana")
            elif item in df['POWIAT'].values:
                if item not in [self.window_locations_list_ui.listWidget_Locatons_List.item(i).text()
                                for i in range(self.window_locations_list_ui.listWidget_Locatons_List.count())]:
                    self.window_locations_list_ui.listWidget_Locatons_List.addItem(item)
                    self.changeColorByName(item, QColor(self.selection_color_rgba[0], self.selection_color_rgba[1],
                                                        self.selection_color_rgba[2], self.selection_color_rgba[3]))
                else:
                    self.label_Location_Error_Message.setText(f"Lokalizacja '{item}' jest już dodana")
            else:
                if self.lineEdit_Location.text() != "":
                    self.label_Location_Error_Message.setText("Nieprawidłowa lokalizacja")

            self.lineEdit_Location.clear()
            self.updateStatusBar()

        except Exception as e:
            print(e)

    def addQCompleterAll(self):
        try:
            df = pd.read_csv("Resources/locations-suggestion.csv", delimiter=';')

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
            self.updateStatusBar()
            self.changeColorByName(item.text(),
                                   QColor(self.map_color_rgba[0], self.map_color_rgba[1], self.map_color_rgba[2],
                                          self.map_color_rgba[3]))

    def handleSelectionChange(self):
        self.window_locations_list_ui.pushButton_Delete.setEnabled(True)

    def generatePdf(self, filePath, districtKey, resultInOneFile, save, targetGroupIndex):
        self.section_pages = {}
        try:
            if filePath:
                if resultInOneFile == True and self.pageCreated == False:
                    self.pdf_canvas = canvas.Canvas(filePath)
                    self.pageCreated = True
                elif resultInOneFile == False:
                    self.pdf_canvas = canvas.Canvas(filePath)

                if QFile.exists(MainController.SETTINGS_FILE):
                    with open(MainController.SETTINGS_FILE, 'r') as file:
                        settings_data = json.load(file)

                self.addTitlePage(self.pdf_canvas, districtKey, targetGroupIndex)

                if settings_data.get("table_of_contents", True):
                    self.addTableOfContents(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("summary", True):
                    self.addSummary(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("introduction", True):
                    self.addIntroduction(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("methodology", True):
                    self.addMethodology(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("description_of_the_location", True):
                    self.addLocationDescription(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("annual_analysis", True):
                    self.addAnnualAnalysis(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("results_and_conclusions", True):
                    self.addResultsAndConclusions(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("recommendations", True):
                    self.addRecommendations(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("additional_customer_specific_content", True):
                    self.addClientSpecificContent(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("report_summary", True):
                    self.addSummaryReport(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("references", True):
                    self.addReferences(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("attachments", True):
                    self.addAttachments(self.pdf_canvas, districtKey, targetGroupIndex)

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

    def draw_centered_strings(self, pdf_canvas, center_x, center_y, lines):

        # Pobierz wysokość tekstu i odstępy między liniami
        text_height = pdf_canvas._fontsize
        line_spacing = 1.2 * text_height

        # Oblicz położenie x dla tekstu wycentrowanego
        center_x -= pdf_canvas.stringWidth(lines[0], pdf_canvas._fontname, pdf_canvas._fontsize) / 2

        # Rysuj każdą linię tekstu jeden pod drugim
        for line in lines:
            pdf_canvas.drawString(center_x, center_y, line)
            center_y -= line_spacing

    def addTitlePage(self, pdf_canvas, districtKey, targetGroupIndex):

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
        #pdf_canvas.drawCentredString(elements_x, elements_y, f"Wybrane powiaty: {', '.join(list_widget_items)}")
        self.draw_centered_strings(pdf_canvas, elements_x, elements_y, list_widget_items)

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
        pdf_canvas.drawCentredString(values_x, values_y - 80, f"Grupa docelowa indeks: {targetGroupIndex}")
        pdf_canvas.drawCentredString(values_x, values_y - 100,
                                     f"Grupa docelowa nazwa: {self.comboBox_Target_Group.currentText()}")

    def addTableOfContents(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Spis treści'] = {'start': start_page, 'end': start_page}

        # ... Add content for the summary section ...
        pdf_canvas.drawString(100, 750, "Spis treści")

        # Update the end page for the section
        self.section_pages['Spis treści']['end'] = self.getCurrentPage()

    def addSummary(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Streszczenie'] = {'start': start_page, 'end': start_page}

        # ... Add content for the summary section ...
        pdf_canvas.drawString(100, 750, "Streszczenie")

        # Update the end page for the section
        self.section_pages['Streszczenie']['end'] = self.getCurrentPage()

    def addIntroduction(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Wprowadzenie'] = {'start': start_page, 'end': start_page}

        # ... Add content for the introduction section ...

        # Update the end page for the section
        self.section_pages['Wprowadzenie']['end'] = self.getCurrentPage()

    def addMethodology(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Metodologia'] = {'start': start_page, 'end': start_page}

        # ... Add content for the methodology section ...

        # Update the end page for the section
        self.section_pages['Metodologia']['end'] = self.getCurrentPage()

    def addLocationDescription(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Opis wybranej lokalizacji'] = {'start': start_page, 'end': start_page}

        # ... Add content for the location description section ...

        # Update the end page for the section
        self.section_pages['Opis wybranej lokalizacji']['end'] = self.getCurrentPage()

    def addAnnualAnalysis(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Analiza roczna'] = {'start': start_page, 'end': start_page}

        # ... Add content for the annual analysis section ...

        # Update the end page for the section
        self.section_pages['Analiza roczna']['end'] = self.getCurrentPage()

    def addResultsAndConclusions(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Wyniki i wnioski'] = {'start': start_page, 'end': start_page}

        # ... Add content for the results and conclusions section ...

        # Update the end page for the section
        self.section_pages['Wyniki i wnioski']['end'] = self.getCurrentPage()

    def addRecommendations(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Zalecenia'] = {'start': start_page, 'end': start_page}

        # ... Add content for the recommendations section ...

        # Update the end page for the section
        self.section_pages['Zalecenia']['end'] = self.getCurrentPage()

    def addClientSpecificContent(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Dodatkowa treść specyficzna dla klienta'] = {'start': start_page, 'end': start_page}

        # ... Add content for the client-specific content section ...

        # Update the end page for the section
        self.section_pages['Dodatkowa treść specyficzna dla klienta']['end'] = self.getCurrentPage()

    def addSummaryReport(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Podsumowanie'] = {'start': start_page, 'end': start_page}

        # ... Add content for the summary report section ...

        # Update the end page for the section
        self.section_pages['Podsumowanie']['end'] = self.getCurrentPage()

    def addReferences(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Referencje'] = {'start': start_page, 'end': start_page}

        # ... Add content for the references section ...

        # Update the end page for the section
        self.section_pages['Referencje']['end'] = self.getCurrentPage()

    def addAttachments(self, pdf_canvas, districtKey, targetGroupIndex):
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
            if fileName:
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
            else:
                self.errorStatus("Nie wybrano miejsca zapisu raportu")


        except Exception as e:
            print(e)

    def errorStatus(self, text="", critical=False):
        try:

            msg = QMessageBox()
            msg.setWindowTitle('DemoG')

            if critical:
                message = f"{text}"
                msg.setIcon(QMessageBox.Icon.Critical)
            else:
                message = f"{text}"
                msg.setIcon(QMessageBox.Icon.Warning)

            msg.setText(message)
            msg.setStandardButtons(QMessageBox.StandardButton.Close)
            msg.button(QMessageBox.StandardButton.Close).setText('Zamknij')

            reply = msg.exec()
            return reply == QMessageBox.StandardButton.Close


        except Exception as e:
            print(e)

    def draw_map_in_graphics_view(self):
        self.items_dict = {}
        self.original_pen = None

        def updateLocationsList(item):
            list_widget = self.window_locations_list_ui.listWidget_Locatons_List
            items = [list_widget.item(i).text() for i in range(list_widget.count())]

            if item in items:
                item_to_remove = list_widget.findItems(item, Qt.MatchFlag.MatchExactly)[0]
                row = list_widget.row(item_to_remove)
                list_widget.takeItem(row)
            else:
                list_widget.addItem(item)

        def geojsonToQtPolygon(geojson):
            polygons = []
            all_points = []
            for feature in geojson['features']:
                if feature['geometry']['type'] == 'Polygon':
                    coordinates = feature['geometry']['coordinates'][0]
                    points = [QPointF(float(x), float(y)) for x, y in map(getCartesian, coordinates)]
                    all_points.extend(points)
                    polygons.append((QPolygonF(points), feature['properties']))
                elif feature['geometry']['type'] == 'MultiPolygon':
                    for polygon in feature['geometry']['coordinates']:
                        coordinates = polygon[0]
                        points = [QPointF(float(x), float(y)) for x, y in map(getCartesian, coordinates)]
                        all_points.extend(points)
                        polygons.append((QPolygonF(points), feature['properties']))
            return polygons, all_points

        def getCartesian(coord):
            lon, lat = np.deg2rad(coord)
            R = 7000  # radius of the earth
            x = R * np.cos(lat) * np.cos(lon)
            y = R * np.cos(lat) * np.sin(lon)
            return x, y

        def changeColorByName(name, color, items_dict):
            for key in items_dict:
                if key.startswith(name):
                    item = items_dict.get(key)
                    if item is not None:
                        item.setBrush(QBrush(QColor(color)))

        def mousePressEvent(item, event):
            name = item.properties["fullname"]
            if item.brush().color() == QColor(self.map_color_rgba[0], self.map_color_rgba[1], self.map_color_rgba[2],
                                              self.map_color_rgba[3]):
                item.setBrush(QBrush(
                    QColor(self.selection_color_rgba[0], self.selection_color_rgba[1], self.selection_color_rgba[2],
                           self.selection_color_rgba[3])))
                changeColorByName(name, QColor(self.selection_color_rgba[0], self.selection_color_rgba[1],
                                               self.selection_color_rgba[2], self.selection_color_rgba[3]),
                                  self.items_dict)
                updateLocationsList(name)

            else:
                item.setBrush(QBrush(QColor(self.map_color_rgba[0], self.map_color_rgba[1], self.map_color_rgba[2],
                                            self.map_color_rgba[3])))
                changeColorByName(name, QColor(self.map_color_rgba[0], self.map_color_rgba[1], self.map_color_rgba[2],
                                               self.map_color_rgba[3]), self.items_dict)
                updateLocationsList(name)

            self.updateStatusBar()

        def hoverEnterEvent(item, event):
            name = item.properties.get('name', '')
            voivodeship = item.properties.get('voivodeship', '')
            tooltip_text = f"<b>Nazwa</b>: {name}<br><br><b>Woj.</b>: {voivodeship}"
            QToolTip.showText(event.screenPos(), tooltip_text)
            item.setPen(QPen(QColor(self.hover_color_rgba[0], self.hover_color_rgba[1], self.hover_color_rgba[2],
                                    self.hover_color_rgba[3]), self.selection_border_size))
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        def hoverLeaveEvent(item, event):
            QToolTip.hideText()
            item.setPen(self.original_pen)
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        def drawPolygons(polygons, center):
            scene = QGraphicsScene()
            items_dict = {}
            name_counts = {}
            for polygon, properties in polygons:
                path = QPainterPath()
                path.addPolygon(polygon.translated(-center))
                item = QGraphicsPathItem(path)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                item.properties = properties
                item.setBrush(QBrush(QColor(self.map_color_rgba[0], self.map_color_rgba[1], self.map_color_rgba[2],
                                            self.map_color_rgba[3])))
                item.setAcceptHoverEvents(True)
                item.setPen(QPen(
                    QColor(self.border_map_color_rgba[0], self.border_map_color_rgba[1], self.border_map_color_rgba[2],
                           self.border_map_color_rgba[3]), self.map_border_size))
                self.original_pen = item.pen()
                setattr(item, 'mousePressEvent', mousePressEvent.__get__(item))
                setattr(item, 'hoverEnterEvent', hoverEnterEvent.__get__(item))
                setattr(item, 'hoverLeaveEvent', hoverLeaveEvent.__get__(item))
                scene.addItem(item)
                name = properties.get('fullname')
                if name in name_counts:
                    name_counts[name] += 1
                    name += f"_{name_counts[name]}"
                else:
                    name_counts[name] = 0
                items_dict[name] = item

            self.items_dict = items_dict
            self.graphicsView_Map.setScene(scene)
            self.graphicsView_Map.scale(1, -1)
            self.graphicsView_Map.rotate(250)
            self.graphicsView_Map.scale(1.5, 1.5)

        with open('./Maps/poland_map_low_quality.geojson', encoding='utf-8') as f:
            geojson = json.load(f)

        polygons, all_points = geojsonToQtPolygon(geojson)
        center = QPointF(sum(p.x() for p in all_points) / len(all_points),
                         sum(p.y() for p in all_points) / len(all_points))
        drawPolygons(polygons, center)
