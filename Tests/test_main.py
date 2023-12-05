import unittest
from unittest.mock import MagicMock, patch
from Controllers.MainController import MainController  # Zaimportuj odpowiedni moduł
from PyQt6.QtWidgets import QApplication
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QPointF, QDate
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QGraphicsScene, QGraphicsPolygonItem
from Views.Main.main_window import Ui_MainWindow_Main
from Views.Main.about_app import Ui_Dialog_About_App
import sys
import os


class TestMainController(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def setUp(self):
        self.controller = MainController()

    @classmethod
    def tearDownClass(cls):
        del cls.app

# Testowanie daty początkowej

    @patch('PyQt6.QtCore.QDate.currentDate')
    def test_populate_date_from(self, mock_current_date):
        mock_current_date.return_value = QDate(2023, 1, 1)
        self.controller.populateDateFrom()
        self.assertEqual(self.controller.comboBox_Date_From.count(), 6) ## czy data początkowa ma 6 wartości (indeksów)

# Testowanie daty końcowej

    @patch('PyQt6.QtCore.QDate.currentDate')
    def test_populate_date_to(self, mock_current_date):
        mock_current_date.return_value = QDate(2023, 1, 1)
        self.controller.populateDateTo()
        self.assertEqual(self.controller.comboBox_Date_To.count(), 11) ## czy data końcowa ma 11 wartości (indeksów)

# Testowanie poprawności dat

    def test_date_from_less_than_date_to(self):
        self.controller.populateDateFrom()
        self.controller.populateDateTo()
        self.controller.comboBox_Date_From.setCurrentIndex(2) ## wybór daty z indeksem 2 w pierwszym boxie
        self.controller.comboBox_Date_To.setCurrentIndex(5) ## wybór daty z indeksem 5 w drugim boxie

        # Sprawdzanie, czy comboBoxy mają ustawione wartości

        if not self.controller.comboBox_Date_From.currentText() or not self.controller.comboBox_Date_To.currentText():
            self.fail("ComboBoxes must have values set before performing this test")

        # Sprawdzanie czy wartość z 1 comboBoxa jest mniejsza od wartości z drugiego

        date_from = int(self.controller.comboBox_Date_From.currentText())
        date_to = int(self.controller.comboBox_Date_To.currentText())

        self.assertLess(date_from, date_to, "Date From should be less than Date To")


# Testowanie czy pole z lokalizacją nie jest puste

    def test_postal_code_not_empty(self):
        # Ustawienie wartości dla celów testu
        self.controller.lineEdit_Postal_Code.setText("12345")

        postal_code = self.controller.lineEdit_Postal_Code.text()
        self.assertIsNotNone(postal_code, "Postal code should not be None")
        self.assertNotEqual(postal_code, "", "Postal code should not be empty")


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

