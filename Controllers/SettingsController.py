import json

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QMainWindow, QColorDialog, QPushButton
from qt_material import QtStyleTools
from PyQt6.QtCore import Qt, QDir, QFile, QTranslator
from Views.Settings.settings_window import Ui_MainWindow_Settings
from xml.etree import ElementTree as ET


class SettingsController(QMainWindow, Ui_MainWindow_Settings, QtStyleTools):
    SETTINGS_FILE = "settings.json"
    CUSTOM_THEM_FILE = "Themes/my_custom.xml"

    def __init__(self, app, translator):
        super().__init__()
        self.app = app
        self.translator = translator
        self.setWindowFlags(
            Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.setupUi(self)

        self.populateLanguage()
        self.populateThemes()
        self.loadSettings()
        self.loadAndApplyCustomStylesheet()
        self.loadLanguage()

        # Connections
        self.comboBox_Theme.currentIndexChanged.connect(self.loadThem)
        self.comboBox_Theme.currentIndexChanged.connect(self.saveSettings)
        self.comboBox_Language.currentIndexChanged.connect(self.saveSettings)
        self.checkBox_Use_Custom_Theme.clicked.connect(self.loadThem)
        self.checkBox_Use_Secondary_Colors.clicked.connect(self.loadThem)
        self.comboBox_Language.currentIndexChanged.connect(self.loadLanguage)
        self.checkBox_Use_Custom_Theme.clicked.connect(self.saveSettings)
        self.checkBox_Use_Secondary_Colors.clicked.connect(self.saveSettings)
        self.radioButton_In_One_File.clicked.connect(self.saveSettings)
        self.radioButton_In_Separate_Files.clicked.connect(self.saveSettings)
        self.comboBox_Model_Prediction.currentIndexChanged.connect(self.saveSettings)
        self.checkBox_1_Table_Of_Contents.clicked.connect(self.saveSettings)
        self.checkBox_2_Summary.clicked.connect(self.saveSettings)
        self.checkBox_3_Introduction.clicked.connect(self.saveSettings)
        self.checkBox_4_Methodology.clicked.connect(self.saveSettings)
        self.checkBox_5_Description_Of_The_Location.clicked.connect(self.saveSettings)
        self.checkBox_6_Annual_Analysis.clicked.connect(self.saveSettings)
        self.checkBox_7_Results_And_Conclusions.clicked.connect(self.saveSettings)
        self.checkBox_8_Recommendations.clicked.connect(self.saveSettings)
        self.checkBox_9_Additional_Customer_Specific_Content.clicked.connect(self.saveSettings)
        self.checkBox_10_Report_Summary.clicked.connect(self.saveSettings)
        self.checkBox_11_References.clicked.connect(self.saveSettings)
        self.checkBox_12_Attachments.clicked.connect(self.saveSettings)

        self.pushButton_Primary_Color.clicked.connect(
            lambda: self.changeColor('primaryColor', 'pushButton_Primary_Color'))
        self.pushButton_Primary_Light_Color.clicked.connect(
            lambda: self.changeColor('primaryLightColor', 'pushButton_Primary_Light_Color'))
        self.pushButton_Secondary_Color.clicked.connect(
            lambda: self.changeColor('secondaryColor', 'pushButton_Secondary_Color'))
        self.pushButton_Secondary_Light_Color.clicked.connect(
            lambda: self.changeColor('secondaryLightColor', 'pushButton_Secondary_Light_Color'))
        self.pushButton_Secondary_Dark_Color.clicked.connect(
            lambda: self.changeColor('secondaryDarkColor', 'pushButton_Secondary_Dark_Color'))
        self.pushButton_Primary_Text_Color.clicked.connect(
            lambda: self.changeColor('primaryTextColor', 'pushButton_Primary_Text_Color'))
        self.pushButton_Secondary_Text_Color.clicked.connect(
            lambda: self.changeColor('secondaryTextColor', 'pushButton_Secondary_Text_Color'))

    def loadLanguage(self):
        language_files = {
            0: "Translations/PL/qtbase_pl.qm",
            1: "Translations/EN/qtbase_en.qm",
        }

        selected_language = self.comboBox_Language.currentIndex()

        selected_language_file = language_files.get(selected_language)
        if selected_language_file:
            if self.translator.load(selected_language_file):
                self.app.installTranslator(self.translator)
        else:
            default_language_file = "Translations/EN/qtbase_en.qm"
            if self.translator.load(default_language_file):
                self.app.installTranslator(self.translator)

    def changeColor(self, field_name, button_name):
        try:
            button = self.findChild(QPushButton, button_name)

            if button:
                current_style = button.styleSheet()

                color = QColorDialog.getColor(options=QColorDialog.ColorDialogOption.ShowAlphaChannel)

                if color.isValid():
                    button.setStyleSheet(f"{current_style}background-color: {color.name()};")

                    custom_colors = self.loadCustomColors(SettingsController.CUSTOM_THEM_FILE)
                    custom_colors[field_name] = color.name()

                    self.saveCustomColors(custom_colors, SettingsController.CUSTOM_THEM_FILE)
                    self.loadThem()
                else:
                    button.setStyleSheet(current_style)

        except Exception as e:
            print(f"Error changing color: {e}")

    def saveCustomColors(self, colors, file_path):
        try:
            root = ET.Element("resources")

            for color_name, color_value in colors.items():
                color_elem = ET.SubElement(root, "color", name=color_name)
                color_elem.text = color_value

            tree = ET.ElementTree(root)

            with open(file_path, 'wb') as file:
                tree.write(file, encoding="utf-8", xml_declaration=True)

        except Exception as e:
            print(f"Error saving custom colors: {e}")

    def loadCustomColors(self, file_path):
        colors = {}
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            for color_elem in root.findall(".//color"):
                color_name = color_elem.get("name")
                color_value = color_elem.text
                colors[color_name] = color_value
        except Exception as e:
            print(f"Error loading custom colors: {e}")
        return colors

    def applyCustomStylesheet(self, custom_stylesheet):
        self.pushButton_Primary_Color.setStyleSheet(
            f"background-color: {custom_stylesheet.get('primaryColor', '#ffffff')};")
        self.pushButton_Primary_Light_Color.setStyleSheet(
            f"background-color: {custom_stylesheet.get('primaryLightColor', '#ffffff')};")
        self.pushButton_Secondary_Color.setStyleSheet(
            f"background-color: {custom_stylesheet.get('secondaryColor', '#ffffff')};")
        self.pushButton_Secondary_Light_Color.setStyleSheet(
            f"background-color: {custom_stylesheet.get('secondaryLightColor', '#ffffff')};")
        self.pushButton_Secondary_Dark_Color.setStyleSheet(
            f"background-color: {custom_stylesheet.get('secondaryDarkColor', '#ffffff')};")
        self.pushButton_Primary_Text_Color.setStyleSheet(
            f"background-color: {custom_stylesheet.get('primaryTextColor', '#ffffff')};")
        self.pushButton_Secondary_Text_Color.setStyleSheet(
            f"background-color: {custom_stylesheet.get('secondaryTextColor', '#ffffff')};")

    def loadAndApplyCustomStylesheet(self):
        file_path = SettingsController.CUSTOM_THEM_FILE
        custom_colors = self.loadCustomColors(file_path)
        self.applyCustomStylesheet(custom_colors)

    def showSettingsWindow(self):
        self.show()

    def populateLanguage(self):
        languages = ["Polski", "English"]

        self.comboBox_Language.clear()
        self.comboBox_Language.addItems(languages)

    def populateThemes(self):
        themes_path = "Themes"
        themes = [entry.replace(".xml", "") for entry in QDir(themes_path).entryList(['*.xml'])]
        themes.remove("my_custom")

        self.comboBox_Theme.clear()
        self.comboBox_Theme.addItems(themes)

    def loadThem(self):
        if self.checkBox_Use_Custom_Theme.isChecked():
            if self.checkBox_Use_Secondary_Colors.isChecked():
                self.apply_stylesheet(self.app, SettingsController.CUSTOM_THEM_FILE, invert_secondary=True)
            else:
                self.apply_stylesheet(self.app, SettingsController.CUSTOM_THEM_FILE)
        else:
            themes_path = "Themes/"
            extension = ".xml"
            them_name = self.comboBox_Theme.currentText()
            filename = themes_path + them_name + extension

            self.apply_stylesheet(self.app, filename)

    def loadSettings(self):
        if QFile.exists(SettingsController.SETTINGS_FILE):
            with open(SettingsController.SETTINGS_FILE, 'r') as file:
                settings = json.load(file)
                language_index = settings.get("language_index", 0)
                theme_index = settings.get("theme_index", 0)
                custom_theme_enabled = settings.get("custom_theme_enabled", False)
                secondary_colors_enabled = settings.get("secondary_colors_enabled", False)
                report_in_many_files = settings.get("report_in_many_files", False)

                table_of_contents = settings.get("table_of_contents", True)
                summary = settings.get("summary", True)
                introduction = settings.get("introduction", True)
                methodology = settings.get("methodology", True)
                description_of_the_location = settings.get("description_of_the_location", True)
                annual_analysis = settings.get("annual_analysis", True)
                results_and_conclusions = settings.get("results_and_conclusions", True)
                recommendations = settings.get("recommendations", True)
                additional_customer_specific_content = settings.get("additional_customer_specific_content", True)
                report_summary = settings.get("report_summary", True)
                references = settings.get("references", True)
                attachments = settings.get("attachments", True)

                self.checkBox_Use_Custom_Theme.setChecked(custom_theme_enabled)
                self.checkBox_Use_Secondary_Colors.setChecked(secondary_colors_enabled)
                self.comboBox_Language.setCurrentIndex(language_index)
                self.comboBox_Theme.setCurrentIndex(theme_index)

                if report_in_many_files:
                    self.radioButton_In_Separate_Files.setChecked(True)
                else:
                    self.radioButton_In_One_File.setChecked(True)

                self.checkBox_1_Table_Of_Contents.setChecked(table_of_contents)
                self.checkBox_2_Summary.setChecked(summary)
                self.checkBox_3_Introduction.setChecked(introduction)
                self.checkBox_4_Methodology.setChecked(methodology)
                self.checkBox_5_Description_Of_The_Location.setChecked(description_of_the_location)
                self.checkBox_6_Annual_Analysis.setChecked(annual_analysis)
                self.checkBox_7_Results_And_Conclusions.setChecked(results_and_conclusions)
                self.checkBox_8_Recommendations.setChecked(recommendations)
                self.checkBox_9_Additional_Customer_Specific_Content.setChecked(additional_customer_specific_content)
                self.checkBox_10_Report_Summary.setChecked(report_summary)
                self.checkBox_11_References.setChecked(references)
                self.checkBox_12_Attachments.setChecked(attachments)

                self.loadThem()
        else:
            default_settings = {"language_index": 1, "theme_index": 1}
            with open(SettingsController.SETTINGS_FILE, 'w') as file:
                json.dump(default_settings, file, indent=2)
            self.loadSettings()

    def saveSettings(self):
        language_index = self.comboBox_Language.currentIndex()
        theme_index = self.comboBox_Theme.currentIndex()
        custom_theme_enabled = self.checkBox_Use_Custom_Theme.isChecked()
        secondary_colors_enabled = self.checkBox_Use_Secondary_Colors.isChecked()
        report_in_many_files = False

        # files
        if self.radioButton_In_One_File.isChecked():
            report_in_many_files = False
        elif self.radioButton_In_Separate_Files.isChecked():
            report_in_many_files = True

        # model
        selected_model_index = self.comboBox_Model_Prediction.currentIndex()
        selected_model_name = self.comboBox_Model_Prediction.currentText()

        # report
        table_of_contents = self.checkBox_1_Table_Of_Contents.isChecked()
        summary = self.checkBox_2_Summary.isChecked()
        introduction = self.checkBox_3_Introduction.isChecked()
        methodology = self.checkBox_4_Methodology.isChecked()
        description_of_the_location = self.checkBox_5_Description_Of_The_Location.isChecked()
        annual_analysis = self.checkBox_6_Annual_Analysis.isChecked()
        results_and_conclusions = self.checkBox_7_Results_And_Conclusions.isChecked()
        recommendations = self.checkBox_8_Recommendations.isChecked()
        additional_customer_specific_content = self.checkBox_9_Additional_Customer_Specific_Content.isChecked()
        report_summary = self.checkBox_10_Report_Summary.isChecked()
        references = self.checkBox_11_References.isChecked()
        attachments = self.checkBox_12_Attachments.isChecked()

        settings = {
            "language_index": language_index,
            "theme_index": theme_index,
            "custom_theme_enabled": custom_theme_enabled,
            "secondary_colors_enabled": secondary_colors_enabled,
            "report_in_many_files": report_in_many_files,
            "selected_model_index": selected_model_index,
            "selected_model_name": selected_model_name,
            "table_of_contents": table_of_contents,
            "summary": summary,
            "introduction": introduction,
            "methodology": methodology,
            "description_of_the_location": description_of_the_location,
            "annual_analysis": annual_analysis,
            "results_and_conclusions": results_and_conclusions,
            "recommendations": recommendations,
            "additional_customer_specific_content": additional_customer_specific_content,
            "report_summary": report_summary,
            "references": references,
            "attachments": attachments
        }

        with open(SettingsController.SETTINGS_FILE, 'w') as file:
            json.dump(settings, file, indent=2)
