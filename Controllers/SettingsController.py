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
        self.checkBox_Use_Custom_Theme.clicked.connect(self.setCustomThem)
        self.checkBox_Use_Secondary_Colors.clicked.connect(self.setCustomThem)
        self.comboBox_Language.currentIndexChanged.connect(self.loadLanguage)

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
            color = QColorDialog.getColor().name()

            if color:
                button = self.findChild(QPushButton, button_name)
                if button:
                    button.setStyleSheet(f"background-color: {color};")

                    custom_colors = self.loadCustomColors(SettingsController.CUSTOM_THEM_FILE)
                    custom_colors[field_name] = color

                    self.saveCustomColors(custom_colors, SettingsController.CUSTOM_THEM_FILE)
                    self.setCustomThem()


        except Exception as e:
            print(f"Error changing color: {e}")

    def saveCustomColors(self, colors, file_path):
        try:
            root = ET.Element("resources")

            for color_name, color_value in colors.items():
                color_elem = ET.SubElement(root, "color", name=color_name)
                color_elem.text = color_value

            tree = ET.ElementTree(root)
            tree.write(file_path, encoding="utf-8", xml_declaration=True)
        except Exception as e:
            print(f"Error saving custom colors: {e}")

    def setCustomThem(self):
        if self.checkBox_Use_Custom_Theme.isChecked():
            if self.checkBox_Use_Secondary_Colors.isChecked():
                self.apply_stylesheet(self.app, SettingsController.CUSTOM_THEM_FILE, invert_secondary=True)
            else:
                self.apply_stylesheet(self.app, SettingsController.CUSTOM_THEM_FILE)
        else:
            self.loadSettings()

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

                self.comboBox_Language.setCurrentIndex(language_index)
                self.comboBox_Theme.setCurrentIndex(theme_index)
                self.loadThem()
        else:
            default_settings = {"language_index": 1, "theme_index": 1}
            with open(SettingsController.SETTINGS_FILE, 'w') as file:
                json.dump(default_settings, file, indent=2)
            self.loadSettings()

    def saveSettings(self):
        language_index = self.comboBox_Language.currentIndex()
        theme_index = self.comboBox_Theme.currentIndex()
        settings = {"language_index": language_index, "theme_index": theme_index}

        with open(SettingsController.SETTINGS_FILE, 'w') as file:
            json.dump(settings, file, indent=2)
