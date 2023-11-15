from PyQt6.QtWidgets import QMainWindow, QDialog
from Views.Main.main_window import Ui_MainWindow_Main
from Views.Settings.settings_general import Ui_Dialog_App_Settings
from Views.Settings.report_content import Ui_Dialog_Report_Content


class MainController(QMainWindow, Ui_MainWindow_Main):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Connections
        self.action_App_Settings.triggered.connect(self.windowAppSettings)
        self.action_Raport_Settings.triggered.connect(self.windowReportContent)
        self.action_Exit.triggered.connect(self.close)

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
