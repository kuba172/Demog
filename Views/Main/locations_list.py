# Form implementation generated from reading ui file '.\locations-list.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog_Location_List(object):
    def setupUi(self, Dialog_Location_List):
        Dialog_Location_List.setObjectName("Dialog_Location_List")
        Dialog_Location_List.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        Dialog_Location_List.resize(800, 600)
        Dialog_Location_List.setMinimumSize(QtCore.QSize(800, 600))
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog_Location_List)
        self.verticalLayout.setObjectName("verticalLayout")
        self.listWidget_Locatons_List = QtWidgets.QListWidget(parent=Dialog_Location_List)
        self.listWidget_Locatons_List.setObjectName("listWidget_Locatons_List")
        self.verticalLayout.addWidget(self.listWidget_Locatons_List)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_Delete = QtWidgets.QPushButton(parent=Dialog_Location_List)
        self.pushButton_Delete.setEnabled(False)
        self.pushButton_Delete.setObjectName("pushButton_Delete")
        self.horizontalLayout.addWidget(self.pushButton_Delete)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton_Cancel = QtWidgets.QPushButton(parent=Dialog_Location_List)
        self.pushButton_Cancel.setObjectName("pushButton_Cancel")
        self.horizontalLayout.addWidget(self.pushButton_Cancel)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog_Location_List)
        QtCore.QMetaObject.connectSlotsByName(Dialog_Location_List)

    def retranslateUi(self, Dialog_Location_List):
        _translate = QtCore.QCoreApplication.translate
        Dialog_Location_List.setWindowTitle(_translate("Dialog_Location_List", "Wybrane lokalizacje"))
        self.pushButton_Delete.setText(_translate("Dialog_Location_List", "Usuń"))
        self.pushButton_Cancel.setText(_translate("Dialog_Location_List", "Anuluj"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog_Location_List = QtWidgets.QDialog()
    ui = Ui_Dialog_Location_List()
    ui.setupUi(Dialog_Location_List)
    Dialog_Location_List.show()
    sys.exit(app.exec())