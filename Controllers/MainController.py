import subprocess

from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QCompleter, QMessageBox, QLabel, QGraphicsScene, \
    QGraphicsView, QApplication, QVBoxLayout, QPushButton, QWidget, QSlider, QGraphicsPathItem, QGraphicsItem, QToolTip
from PyQt6.QtGui import QPolygonF, QPainterPath, QPen, QBrush, QColor, QCursor, QMovie
from PyQt6.QtCore import Qt, QDate, QFile, QPointF, QRect, QSize
from Views.Main.main_window import Ui_MainWindow_Main
from Views.Main.about_app import Ui_Dialog_About_App
from Views.Main.locations_list import Ui_Dialog_Location_List
from Views.Main.loading_window import Ui_Dialog_Loading
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

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, \
    BaseDocTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4

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

        self.pushButton_Zoom_In.clicked.connect(self.zoomIn)
        self.pushButton_Zoom_Out.clicked.connect(self.zoomOut)
        self.horizontalSlider_Map_Size.valueChanged.connect(self.updateZoomValueLabel)

        self.horizontalSlider_Map_Size.setRange(50, 1000)
        self.horizontalSlider_Map_Size.setValue(100)
        self.horizontalSlider_Map_Size.valueChanged.connect(self.zoomMap)

        # self.draw_map_in_graphics_view()

        # Test
        # self.updateMapSettings([223, 75, 23, 255], [0, 0, 0, 255], [22, 0, 220, 255], [0, 0, 255, 255], 3, 3)

        self.show()

    def zoomOut(self):
        self.horizontalSlider_Map_Size.setValue(self.horizontalSlider_Map_Size.value() - 10)

    def zoomIn(self):
        self.horizontalSlider_Map_Size.setValue(self.horizontalSlider_Map_Size.value() + 10)

    def updateZoomValueLabel(self, value):
        self.label_Zoom_Value_Text.setText(f"{str(value)}%")

    def createLoadingWindow(self):
        self.window_loading = QDialog()
        self.window_loading_ui = Ui_Dialog_Loading()
        self.window_loading_ui.setupUi(self.window_loading)
        self.window_loading.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.window_loading.setModal(True)
        self.window_loading.setWindowOpacity(0)
        time = round(float(self.reportTimeNumber) / 60)

        i = 0
        timeWords = ["minutę", "minuty", "minut"]

        if time <= 1:
            i = 0
        elif 1 < time <= 5:
            i = 1
        else:
            i = 2

        if time == 0:
            time = 0.5
            i = 1

        text = f"Proszę czekać, może to potrwać nawet {time} {timeWords[i]}..."
        self.window_loading_ui.label_Dynamic_Text.setText(text)

        self.window_loading.show()

        return True

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
            self.reportTimeNumber = newValue * yearDifference * estimatedTime
            self.reportGenerationTime.setText(
                f"Szacunkowy czas generowania raportu: {self.reportTimeNumber} sekund    ")
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
                targetGroup = data.get("targetGroup", "")

                if dateFrom in [self.comboBox_Date_From.itemText(i) for i in range(self.comboBox_Date_From.count())]:
                    index = self.comboBox_Date_From.findText(dateFrom)
                    self.comboBox_Date_From.setCurrentIndex(index)

                if dateTo in [self.comboBox_Date_To.itemText(i) for i in range(self.comboBox_Date_To.count())]:
                    index = self.comboBox_Date_To.findText(dateTo)
                    self.comboBox_Date_To.setCurrentIndex(index)

                if targetGroup in [self.comboBox_Target_Group.itemText(i) for i in
                                   range(self.comboBox_Target_Group.count())]:
                    index = self.comboBox_Target_Group.findText(targetGroup)
                    self.comboBox_Target_Group.setCurrentIndex(index)

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
                # print(fileName[0])
            elif fileName[0]:
                print("Not supported extension")

        except Exception as e:
            print(e)

    def save(self, filePath):
        dateFrom = self.comboBox_Date_From.currentText()
        dateTo = self.comboBox_Date_To.currentText()
        districtsList = [self.window_locations_list_ui.listWidget_Locatons_List.item(i).text() for i in
                         range(self.window_locations_list_ui.listWidget_Locatons_List.count())]
        targetGroup = self.comboBox_Target_Group.currentText()

        dataDump = {}

        dataDump["targetGroup"] = targetGroup
        dataDump["dateFrom"] = dateFrom
        dataDump["dateTo"] = dateTo
        dataDump["districtsList"] = districtsList

        if filePath:
            with open(filePath, "w") as file:
                json.dump(dataDump, file)

            self.setSavedFilePath(filePath)

        # print(dateFrom, dateTo, districtsList)
        # print(dataDump)

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
            loadingResult = None

            resultCheckDistrict = self.checkDistrict()
            resultCheckDate = self.checkDate()
            resultCheckTargetGroup = self.checkTargetGroup()

            districktKeys = None
            extensionPDF = ".pdf"

            if resultCheckDistrict and resultCheckDate and resultCheckTargetGroup:

                loadingResult = self.createLoadingWindow()

                if self.resultInManyFiles():
                    directoryPath = self.getDirectoryPath()
                    self.window_loading.setWindowOpacity(1)
                else:
                    filePath = self.getFileNamePath()
                    self.window_loading.setWindowOpacity(1)

                if not filePath and not directoryPath:
                    self.window_loading.close()

                if (filePath or directoryPath) and loadingResult == True:

                    self.runModel()
                    districktKeys = DataStorageModel.get_all_keys()
                    districktKeys.pop(0)
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

                    self.window_loading.close()
                    self.statusConfirmation(filePath, success=success, isDir=False)
                    self.updateReportField()

                    return success
                elif directoryPath:
                    for key in districktKeys:
                        filePath = f"{directoryPath}/{key}{extensionPDF}"
                        success = self.generatePdf(filePath, key, resultInOneFile=False, save=True,
                                                   targetGroupIndex=targetGroupIndex)

                    self.window_loading.close()
                    self.statusConfirmation(filePath, success=success, isDir=True)
                    self.updateReportField()

                    return success
                else:
                    self.window_loading.close()
                    return False
            elif resultCheckDistrict == False and resultCheckDate == False and resultCheckTargetGroup == False:
                self.errorStatus("Wybierz lokalizację, przedział czasowy oraz segment docelowy")
            elif resultCheckDistrict == False and resultCheckDate == False and resultCheckTargetGroup == True:
                self.errorStatus("Wybierz lokalizację oraz przedział czasowy")
            elif resultCheckDistrict == False and resultCheckDate == True and resultCheckTargetGroup == False:
                self.errorStatus("Wybierz lokalizację oraz segment docelowy")
            elif resultCheckDistrict == True and resultCheckDate == False and resultCheckTargetGroup == False:
                self.errorStatus("Wybierz przedział czasowy oraz segment docelowy")
            elif resultCheckDistrict == False:
                self.errorStatus("Wybierz lokalizację")
            elif resultCheckDate == False:
                self.errorStatus("Wybierz przedział czasowy")
            elif resultCheckTargetGroup == False:
                self.errorStatus("Wybierz segment docelowy")
            else:
                self.errorStatus("Coś poszło nie tak", critical=True)

            return False

        except Exception as e:
            self.window_loading.close()
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
                    self.changeColorByName(powiat_value,
                                           QColor(self.selection_color_rgba[0], self.selection_color_rgba[1],
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
                    self.pdf_canvas = canvas.Canvas(filePath, pagesize=A4)
                    self.pageCreated = True
                elif resultInOneFile == False:
                    self.pdf_canvas = canvas.Canvas(filePath, pagesize=A4)

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
                if settings_data.get("annual_analysis", True):
                    self.addAnnualAnalysis(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("recommendations", True):
                    self.addRecommendations(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("report_summary", True):
                    self.addSummaryReport(self.pdf_canvas, districtKey, targetGroupIndex)
                if settings_data.get("references", True):
                    self.addReferences(self.pdf_canvas, districtKey, targetGroupIndex)

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

    def draw_paragraph(canvas, paragraph, x, y, width):
        page_width, page_height = A4
        margin = 72
        paragraph.wrapOn(canvas, width, page_height)
        paragraph.drawOn(canvas, x, y)
        return y - paragraph.height  # Update Y to the position after the paragraph

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
        page_width, page_height = A4
        margin = inch
        image_width = 1.5 * inch  # Adjust as needed
        image_height = 1.3 * inch  # Adjust as needed

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
        pdf_canvas.drawCentredString(title_x, title_y - 30, f"Kompleksowa analiza")

        # Date of Report Generation
        pdf_canvas.setFont("DejaVuSans", 12)
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        date_x = page_width / 2
        date_y = title_y - 60  # Adjust as needed
        pdf_canvas.drawCentredString(date_x, date_y, f"Data wygenerowania raportu: {current_date}")

        # Selected Districts
        pdf_canvas.setFont("DejaVuSans", 12)
        # list_widget_items = [self.window_locations_list_ui.listWidget_Locatons_List.item(i).text() for i in
        # range(self.window_locations_list_ui.listWidget_Locatons_List.count())]
        elements_x = page_width / 2
        elements_y = date_y - 30  # Adjust as needed
        # pdf_canvas.drawCentredString(elements_x, elements_y, f"Wybrane powiaty: {', '.join(list_widget_items)}")
        # self.draw_centered_strings(pdf_canvas, elements_x, elements_y, list_widget_items)

        # Selected dates
        pdf_canvas.setFont("DejaVuSans", 12)
        combo1_value = self.comboBox_Date_From.currentText()
        combo2_value = self.comboBox_Date_To.currentText()
        values_x = page_width / 2
        values_y = elements_y - 20  # Adjust as needed
        pdf_canvas.drawCentredString(values_x, values_y,
                                     f"Wybrany przedział czasowy: od roku {combo1_value} do roku {combo2_value}")

        modelName = self.getModelName()
        pdf_canvas.drawCentredString(values_x, values_y - 20, f"Wybrany model: {modelName}")
        pdf_canvas.drawCentredString(values_x, values_y - 40, f"Aktulany powiat: {districtKey}")
        # pdf_canvas.drawCentredString(values_x, values_y - 80, f"Grupa docelowa indeks: {targetGroupIndex}")
        pdf_canvas.drawCentredString(values_x, values_y - 60,
                                     f"Grupa docelowa: {self.comboBox_Target_Group.currentText()}")

    def addTableOfContents(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Spis treści'] = {'start': start_page, 'end': start_page}

        heading_style = ParagraphStyle(name='Heading', fontName='DejaVuSans-Bold', fontSize=18, leading=15,
                                       alignment=TA_CENTER)
        header_text = "Spis treści"
        header_paragraph = Paragraph(header_text, heading_style)

        page_width, page_height = A4

        x_position = (page_width - 450) / 2  # Adjust width as necessary for your layout
        y_position = page_height - 50  # Adjust this value to move the header up or down

        header_paragraph.wrapOn(pdf_canvas, 450, 100)  # Width and height for wrapping
        header_paragraph.drawOn(pdf_canvas, x_position, y_position)

        # Update the end page for the section
        self.section_pages['Spis treści']['end'] = self.getCurrentPage()

    def addSummary(self, pdf_canvas, districtKey, targetGroupIndex):
        self.start_new_page(pdf_canvas)
        start_page = self.getCurrentPage()
        self.section_pages['Streszczenie'] = {'start': start_page, 'end': start_page}

        heading_style = ParagraphStyle(name='Heading', fontName='DejaVuSans-Bold', fontSize=18, leading=15,
                                       alignment=TA_CENTER)
        header_text = "Streszczenie"
        header_paragraph = Paragraph(header_text, heading_style)

        page_width, page_height = A4

        x_position = (page_width - 450) / 2  # Adjust width as necessary for your layout
        y_position = page_height - 50  # Adjust this value to move the header up or down

        header_paragraph.wrapOn(pdf_canvas, 450, 100)  # Width and height for wrapping
        header_paragraph.drawOn(pdf_canvas, x_position, y_position)

        style2 = ParagraphStyle(name='Normal', fontName='DejaVuSans', fontSize=12, leading=15, alignment=TA_JUSTIFY)
        msg2 = f"""Wprowadzenie do raportu predykcyjnego dotyczącego danych demograficznych dla: {districtKey} w danym odstępie czasowym stanowi dogłębne spojrzenie na przyszłość społeczności. Program, oparty na zaawansowanych algorytmach, analizuje wielorakie czynniki wpływające na dynamikę populacyjną, dostarczając prognoz zmian w strukturze demograficznej. Raport nie tylko przewiduje liczbę mieszkańców, lecz również identyfikuje kluczowe czynniki kształtujące te zmiany, dostarczając cennych informacji dla lokalnych władz i decydentów. Obejmując równowagę płci, strukturę wiekową oraz rekomendacje polityki publicznej, raport staje się nieocenionym narzędziem wspierającym podejmowanie strategicznych decyzji na rzecz zrównoważonego rozwoju społeczności."""
        msg_paragraph = Paragraph(msg2, style2)
        width = 450  # Width in points - adjust as needed
        height = 500  # Starting height position - adjust as needed
        msg_paragraph.wrapOn(pdf_canvas, width, height)
        msg_paragraph.drawOn(pdf_canvas, 80, height)

        # Update the end page for the section
        self.section_pages['Streszczenie']['end'] = self.getCurrentPage()

    def addIntroduction(self, pdf_canvas, districtKey, targetGroupIndex):
        try:
            self.start_new_page(pdf_canvas)
            start_page = self.getCurrentPage()
            self.section_pages['Wprowadzenie'] = {'start': start_page, 'end': start_page}

            subsection_style = ParagraphStyle(
                name='Subsection',
                fontName='DejaVuSans-Bold',
                fontSize=14,
                leading=17,
                alignment=TA_LEFT)

            content_style = ParagraphStyle(name='Normal', fontName='DejaVuSans', fontSize=12, leading=15,
                                           alignment=TA_JUSTIFY)
            heading_style = ParagraphStyle(name='Heading', fontName='DejaVuSans-Bold', fontSize=18, leading=15,
                                           alignment=TA_CENTER)

            header_text = "Wprowadzenie"
            header_paragraph = Paragraph(header_text, heading_style)

            page_width, page_height = A4

            x_position = (page_width - 450) / 2  # Adjust width as necessary for your layout
            y_position = page_height - 50  # Adjust this value to move the header up or down

            header_paragraph.wrapOn(pdf_canvas, 450, 100)  # Width and height for wrapping
            header_paragraph.drawOn(pdf_canvas, x_position, y_position)

            subsection1 = Paragraph("Kontekst i cel badania", subsection_style)
            content1 = Paragraph(
                "Niniejszy projekt jest pionierską aplikacją, która wykorzystuje moc uczenia maszynowego do przewidywania danych demograficznych dla określonych lokalizacji w Polsce w wybranych okresach czasu. Opracowana przy użyciu języka Python i integrująca różne potężne biblioteki, takie jak PyQt6, qt-material, pandas, matplotlib, reportlab, plotnine i scikit-learn, ma na celu zapewnienie dokładnego, opartego na danych wglądu w trendy demograficzne. Głównym celem aplikacji jest pomoc w analizie demograficznej poprzez oferowanie prognoz opartych na danych historycznych. Jest to szczególnie przydatne dla urbanistów, decydentów, demografów i badaczy, którzy potrzebują zrozumienia dynamiki populacji w celu podejmowania świadomych decyzji. Przyjazny dla użytkownika interfejs pozwala użytkownikom wybrać lokalizację i analizować dane dla wybranego okresu, dzięki czemu jest to narzędzie dostępne dla szerokiego grona odbiorców.",
                content_style)

            subsection1.wrapOn(pdf_canvas, 450, 100)  # Width and height for wrapping
            subsection1.drawOn(pdf_canvas, x_position, y_position - 20)

            content1.wrapOn(pdf_canvas, 450, 100)  # Width and height for wrapping
            content1.drawOn(pdf_canvas, x_position, y_position - 300)

            self.section_pages['Wprowadzenie']['end'] = self.getCurrentPage()
        except Exception as e:
            print("1" + str(e))

    def addMethodology(self, pdf_canvas, districtKey, targetGroupIndex):
        try:
            self.start_new_page(pdf_canvas)
            start_page = self.getCurrentPage()
            self.section_pages['Metodologia'] = {'start': start_page, 'end': start_page}

            subsection_style = ParagraphStyle(
                name='Subsection',
                fontName='DejaVuSans-Bold',  # Bold font for subsections
                fontSize=14,  # Slightly larger than normal text
                leading=17,
                alignment=TA_LEFT  # Left-aligned
            )
            content_style = ParagraphStyle(name='Normal', fontName='DejaVuSans', fontSize=12, leading=15,
                                           alignment=TA_JUSTIFY)
            heading_style = ParagraphStyle(name='Heading', fontName='DejaVuSans-Bold', fontSize=18, leading=15,
                                           alignment=TA_CENTER)
            header_text = "Metodologia"
            header_paragraph = Paragraph(header_text, heading_style)

            page_width, page_height = A4

            x_position = (page_width - 450) / 2  # Adjust width as necessary for your layout
            y_position = page_height - 50  # Adjust this value to move the header up or down

            header_paragraph.wrapOn(pdf_canvas, 450, 100)  # Width and height for wrapping
            header_paragraph.drawOn(pdf_canvas, x_position, y_position)

            subsection2 = Paragraph("Źródło danych", subsection_style)
            content2 = Paragraph(
                "Dane demograficzne wykorzystane w tej aplikacji pochodzą z Głównego Urzędu Statystycznego w Polsce. Dane te są znane ze swojej wiarygodności i kompleksowego pokrycia statystyk ludności w Polsce.",
                content_style)

            subsection3 = Paragraph("Techniki uczenia maszynowego", subsection_style)
            content3 = Paragraph(
                "Aplikacja wykorzystuje kilka modeli uczenia maszynowego do analizy i przewidywania danych demograficznych:\n\n- Random Forest Regression: Metoda uczenia zespołowego stosowana do regresji. Działa poprzez konstruowanie wielu drzew decyzyjnych w czasie szkolenia i wyprowadzanie średniej prognozy poszczególnych drzew.\n\n- Regresja wielomianowa: Forma analizy regresji, w której związek między zmienną niezależną a zmienną zależną jest modelowany jako wielomian n-tego stopnia.\n\n- Regresja liniowa: Podstawowy i powszechnie stosowany rodzaj analizy predykcyjnej, który zakłada liniową zależność między zmiennymi wejściowymi (X) a pojedynczą zmienną wyjściową (Y).",
                content_style)

            subsection4 = Paragraph("Kryteria i przebieg procesu", subsection_style)
            content4 = Paragraph(
                "Wybór tych modeli opiera się na ich zdolności do obsługi dużych zbiorów danych i zapewniania dokładnych prognoz. Proces obejmuje szkolenie tych modeli na historycznych danych demograficznych, a następnie wykorzystanie ich do przewidywania przyszłych trendów.",
                content_style)

            subsection2.wrapOn(pdf_canvas, 450, 100)  # Width and height for wrapping
            subsection2.drawOn(pdf_canvas, x_position, y_position - 50)

            content2.wrapOn(pdf_canvas, 450, 100)  # Width and height for wrapping
            content2.drawOn(pdf_canvas, x_position, y_position - 200)

            subsection3.wrapOn(pdf_canvas, 450, 100)  # Width and height for wrapping
            subsection3.drawOn(pdf_canvas, x_position, y_position - 250)

            content3.wrapOn(pdf_canvas, 450, 100)  # Width and height for wrapping
            content3.drawOn(pdf_canvas, x_position, y_position - 400)

            subsection4.wrapOn(pdf_canvas, 450, 100)  # Width and height for wrapping
            subsection4.drawOn(pdf_canvas, x_position, y_position - 450)

            content4.wrapOn(pdf_canvas, 450, 100)  # Width and height for wrapping
            content4.drawOn(pdf_canvas, x_position, y_position - 600)

            # Update the end page for the section
            self.section_pages['Metodologia']['end'] = self.getCurrentPage()
        except Exception as e:
            print("2" + str(e))

    # def calculate_attractiveness(self, districtKey, targetGroupIndex):
    #     try:
    #         districtKeys = DataStorageModel.get_all_keys_for_the_same_districts(districtKey)
    #         attractiveness = []
    #         for key in districtKeys:
    #             data_frame = DataStorageModel.get(key)
    #             attr = 0.5  # wzór
    #             print(attr)
    #             attractiveness.append(attr)
    #         return attractiveness
    #     except Exception as e:
    #         print("3" + str(e))

    def get_xy(self, targetGroupIndex):
        x = [0, 19, 65]
        y = [18, 64, 70]
        if targetGroupIndex == 0:
            tab = [x[0], y[0], x[1], y[1], x[2], y[2]]
        elif targetGroupIndex == 1:
            tab = [x[1], y[1], x[0], y[0], x[2], y[2]]
        else:
            tab = [x[2], y[2], x[1], y[1], x[0], y[0]]
        return tab

    def podziel_elementy(self, lista):
        nowa_lista = []
        for i in range(0, len(lista)):
            if i + 1 < len(lista) and lista[i + 1] != 0:
                wynik = lista[i] / lista[i + 1]
            else:
                wynik = lista[i] / 1
            nowa_lista.append(wynik)
        return nowa_lista

    def calculate_attractiveness(self, districtKey, targetGroupIndex):
        try:
            districtKeys = DataStorageModel.get_all_keys_for_the_same_districts(districtKey)
            attractiveness = []
            sum_target_ludzie = []
            sum_other_ludzie = []
            tab = self.get_xy(targetGroupIndex)

            for key in districtKeys:
                data_frame = DataStorageModel.get(key)
                target_result = data_frame[data_frame['wiek'].between(tab[0], tab[1])]['ludzie'].sum()  # waga 0,6
                other_result = data_frame[data_frame['wiek'].between(tab[2], tab[3])]['ludzie'].sum() + \
                               data_frame[data_frame['wiek'].between(tab[4], tab[5])]['ludzie'].sum()  # waga 0,4
                sum_target_ludzie.append(target_result)
                sum_other_ludzie.append(other_result)

            target_wsp = self.podziel_elementy(sum_target_ludzie)
            other_wsp = self.podziel_elementy(sum_other_ludzie)
            print(target_wsp, other_wsp, "TEST WSP")
            # for i in range(len(sum_target_ludzie)):
            #     attr = sum_target_ludzie[i]
            #     attractiveness.append(attr)
            # print(attractiveness, "Test -1")
            return target_wsp
        except Exception as e:
            print("3" + str(e))

    def addAnnualAnalysis(self, pdf_canvas, districtKey, targetGroupIndex):
        try:
            self.start_new_page(pdf_canvas)
            start_page = self.getCurrentPage()
            self.section_pages['Analiza roczna'] = {'start': start_page, 'end': start_page}

            districtKeys = DataStorageModel.get_all_keys()
            print(districtKeys)

            data_frame = DataStorageModel.get(districtKey)

            styles = getSampleStyleSheet()
            title = "Analiza roczna dla powiatu: {}".format(districtKey)
            title_paragraph = Paragraph(title, styles['Heading1'])
            title_paragraph.wrapOn(pdf_canvas, 450, 200)
            title_paragraph.drawOn(pdf_canvas, 50, 750)

            # Adding the table
            data = [["Wiek", "Ludzie", "Mężczyźni", "Kobiety", "Miasto_ludzie", "Miasto_mężczyźni", "Miasto_kobiety",
                     "Wieś_ludzie", "Wieś_mężczyźni", "Wieś_kobiety"]] + data_frame.values.tolist()
            width, height = A4

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            required_width, required_height = table.wrap(0, 0)
            left_margin = 50
            right_margin = 50
            top_margin = 50
            bottom_margin = 50
            available_width = width - left_margin - right_margin
            available_height = height - top_margin - bottom_margin
            scale_factor = min(available_width / required_width, available_height / required_height)
            centered_x_position = left_margin + (available_width - (required_width * scale_factor)) / 2
            centered_y_position = bottom_margin + (available_height - (required_height * scale_factor)) / 2
            pdf_canvas.saveState()
            pdf_canvas.translate(centered_x_position, centered_y_position)
            pdf_canvas.scale(scale_factor, scale_factor)
            table.drawOn(pdf_canvas, 0, 0)
            pdf_canvas.restoreState()

            # Adding the graph
            plt.figure(figsize=(6, 4))
            plt.bar(data_frame['wiek'], data_frame['ludzie'], label='Total Population')
            plt.xlabel('Age')
            plt.ylabel('Population')
            plt.title('Population by Age in ' + districtKey)
            plt.legend()

            # Saving the plot to a BytesIO object
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='PNG')
            img_buffer.seek(0)
            img = Image(img_buffer)
            img.drawHeight = 4 * inch
            img.drawWidth = 6 * inch
            img.wrapOn(pdf_canvas, 450, 200)
            img.drawOn(pdf_canvas, 50, 300)

            # Update the end page for the section
            self.section_pages['Analiza roczna']['end'] = self.getCurrentPage()
        except Exception as e:
            print("4" + str(e))

    def addSummaryReport(self, pdf_canvas, districtKey, targetGroupIndex):
        try:
            self.start_new_page(pdf_canvas)
            start_page = self.getCurrentPage()
            self.section_pages['Podsumowanie'] = {'start': start_page, 'end': start_page}

            pdf_canvas.setFont("DejaVuSans", 9)

            styles = getSampleStyleSheet()
            report_title = "Podsumowanie i wnioski dla lokalizacji: {}".format(districtKey)
            report_paragraph = Paragraph(report_title, styles['Normal'])
            report_paragraph.wrapOn(pdf_canvas, 450, 200)
            report_paragraph.drawOn(pdf_canvas, 50, 750)

            # Add content for the summary report section
            summary_text = "Ta sekcja zawiera przegląd współczynnika atrakcyjności biznesowej dla wybranej dzielnicy i okresu."
            summary_paragraph = Paragraph(summary_text, styles['Normal'])
            summary_paragraph.wrapOn(pdf_canvas, 450, 200)
            summary_paragraph.drawOn(pdf_canvas, 50, 720)

            # Example data - replace with actual data
            print(self.comboBox_Date_From.currentText)
            data = [['Rok', 'Współczynnik atrakcyjności biznesowej']]
            combo1_value = self.comboBox_Date_From.currentText()
            combo1_value = int(combo1_value)
            combo2_value = self.comboBox_Date_To.currentText()
            combo2_value = int(combo2_value)
            years = []
            for i in range(combo1_value, combo2_value + 1):
                years.append(i)
            print(years, "Test0")
            attractiveness_factor = self.calculate_attractiveness(districtKey, targetGroupIndex)
            print(attractiveness_factor, "Test1")
            for i, year in enumerate(years):
                data.append([year, attractiveness_factor[i]])

            # Creating a table for data
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            table.wrapOn(pdf_canvas, 450, 200)
            table.drawOn(pdf_canvas, 50, 600)

            # Update the end page number for the summary section
            self.section_pages['Podsumowanie']['end'] = self.getCurrentPage()
        except Exception as e:
            print("5" + str(e))

    def addRecommendations(self, pdf_canvas, districtKey, targetGroupIndex):
        try:
            self.start_new_page(pdf_canvas)
            start_page = self.getCurrentPage()
            self.section_pages['Zalecenia'] = {'start': start_page, 'end': start_page}

            styles = getSampleStyleSheet()
            report_title = "Zalecenia dla lokalizacji: {}".format(districtKey)
            report_paragraph = Paragraph(report_title, styles['Heading1'])
            report_paragraph.wrapOn(pdf_canvas, 450, 200)
            report_paragraph.drawOn(pdf_canvas, 50, 750)

            attractiveness_factor = self.calculate_attractiveness(districtKey, targetGroupIndex)
            end_factor = np.mean(attractiveness_factor)
            # Generating recommendations based on the business attractiveness factor
            if end_factor > 0.75:
                recommendation_text = "Powiat jest bardzo atrakcyjną lokalizacją dla nowych firm, wykazując obiecujące trendy demograficzne na przyszłość dla wybranego przedziału czasowego."
            elif 0.25 < end_factor <= 0.75:
                recommendation_text = "Powiat jest umiarkowanie atrakcyjną lokalizacją, ale należy dokładnie rozważyć potencjalne zagrożenia dla wybranego przedziału czasowego."
            else:  # attractiveness_factor <= 0.24
                recommendation_text = "Obecnie powiat ten stanowi poważne wyzwanie dla rozwoju nowych firm i może nie być idealnym wyborem dla wybranego przedziału czasowego."

            recommendation_paragraph = Paragraph(recommendation_text, styles['Normal'])
            recommendation_paragraph.wrapOn(pdf_canvas, 450, 200)
            recommendation_paragraph.drawOn(pdf_canvas, 50, 720)

            # Update the end page for the section
            self.section_pages['Zalecenia']['end'] = self.getCurrentPage()
        except Exception as e:
            print("6" + str(e))

    def addReferences(self, pdf_canvas, districtKey, targetGroupIndex):
        try:
            self.start_new_page(pdf_canvas)
            start_page = self.getCurrentPage()
            self.section_pages['Referencje'] = {'start': start_page, 'end': start_page}

            # Aby zapewnić rzetelność i wiarygodność badania, odwołano się do następujących źródeł:
            # Główny Urząd Statystyczny (Central Statistical Office) - Poland:
            # Strona internetowa: stat.gov.pl

            # "Random Forests" - Leo Breiman, Adele Cutler

            # "An Introduction to Statistical Learning" - Gareth James, Daniela Witten, Trevor Hastie, Robert Tibshirani

            # Scikit-Learn Documentation:
            # Strona internetowa: scikit-learn.org/stable

            # Python - dokumentacja dla Pandas, Matplotlib, i innych użytych bibliotek:
            # Python Official Documentation: python.org/doc
            # Pandas Documentation: pandas.pydata.org/pandas-docs/stable
            # Matplotlib Documentation: matplotlib.org/stable/users/index.html

            # Update the end page for the section
            self.section_pages['Referencje']['end'] = self.getCurrentPage()
        except Exception as e:
            print("7" + str(e))

    def addPlot(self, dane, key):
        dane = Models.data_storage_model.DataStorageModel.get(key)
        ggplot(dane)

    def statusConfirmation(self, fileName, success=True, isDir=False):
        try:

            if fileName:
                filePath = fileName
                folderPath = os.path.dirname(filePath)
                fileName = os.path.basename(fileName)
                msg = QMessageBox()
                msg.setWindowTitle('DemoG')

                if success and isDir == False:
                    message = f"Raport '{fileName}' został pomyślnie wygenerowany."
                    msg.setIcon(QMessageBox.Icon.Information)
                elif success and isDir == True:
                    message = f"Raporty zostały pomyślnie wygenerowane w folderze:\n{folderPath}"
                    msg.setIcon(QMessageBox.Icon.Information)
                else:
                    message = f"Błąd podczas generowania raportu '{fileName}'."
                    msg.setIcon(QMessageBox.Icon.Warning)

                msg.setText(message)
                msg.setStandardButtons(QMessageBox.StandardButton.Close | QMessageBox.StandardButton.Open)
                msg.button(QMessageBox.StandardButton.Close).setText('Zamknij')
                msg.button(QMessageBox.StandardButton.Open).setText('Otwórz')

                reply = msg.exec()

                if reply == QMessageBox.StandardButton.Open and isDir == True and success == True:
                    self.openPdfDir(folderPath)
                    return reply == QMessageBox.StandardButton.Close
                elif reply == QMessageBox.StandardButton.Open and isDir == False and success == True:
                    self.openPdf(filePath)
                    return reply == QMessageBox.StandardButton.Close
                elif reply == QMessageBox.StandardButton.Close:
                    return reply == QMessageBox.StandardButton.Close
                else:
                    self.errorStatus("Nie wybrano miejsca zapisu raportu")
        except Exception as e:
            print(e)

    def openPdfDir(self, filePath):
        os.startfile(filePath)

    def openPdf(self, filePath):
        os.startfile(filePath)

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
            tooltip_text = f"<b>Nazwa</b>: {name}<br><br><b>województwo</b>: {voivodeship}"
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
