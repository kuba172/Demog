import os
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QGraphicsScene, QGraphicsPolygonItem
from Views.Main.main_window import Ui_MainWindow_Main
from Views.Settings.settings_general import Ui_Dialog_App_Settings
from Views.Settings.report_content import Ui_Dialog_Report_Content
import geopandas as gpd


class MainController(QMainWindow, Ui_MainWindow_Main):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Connections
        self.action_App_Settings.triggered.connect(self.windowAppSettings)
        self.action_Raport_Settings.triggered.connect(self.windowReportContent)
        self.action_Exit.triggered.connect(self.close)
        self.pushButton_Generate_Report.clicked.connect(self.generateReport)
        path = "Models/Maps/powiaty.shp"
        self.load_shapefile(path)
        self.showMaximized()
        self.show()

    def windowAppSettings(self):
        self.window_app_settings = QDialog()
        self.window_app_settings_ui = Ui_Dialog_App_Settings()
        self.window_app_settings_ui.setupUi(self.window_app_settings)
        self.window_app_settings.show()

    def windowReportContent(self):
        self.window_report_content = QDialog()
        self.window_report_content_ui = Ui_Dialog_Report_Content()
        self.window_report_content_ui.setupUi(self.window_report_content)
        self.window_report_content.show()

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

    def load_shapefile(self, filepath):
        gdf = gpd.read_file(filepath)

        self.graphicsScene = QGraphicsScene()
        self.graphicsView_Interactive_Map.setScene(self.graphicsScene)

        scale_factor = 0.001
        for index, row in gdf.iterrows():
            geometry = row['geometry']
            if geometry.geom_type == 'Polygon':
                polygon = QGraphicsPolygonItem()
                points = [QPointF(point[0] * scale_factor, -point[1] * scale_factor) for point in
                          geometry.exterior.coords]
                polygon.setPolygon(QtGui.QPolygonF(points))
                polygon.setBrush(QBrush(Qt.GlobalColor.blue))
                polygon.setPen(QPen(QColor(0, 0, 0), 1))
                self.graphicsScene.addItem(polygon)
