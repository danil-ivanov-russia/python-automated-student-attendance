# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog_bd_connection.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_dialog_db_connection(object):
    def setupUi(self, dialog_db_connection):
        dialog_db_connection.setObjectName("dialog_db_connection")
        dialog_db_connection.resize(320, 240)
        self.le_db_host = QtWidgets.QLineEdit(dialog_db_connection)
        self.le_db_host.setGeometry(QtCore.QRect(20, 30, 281, 20))
        self.le_db_host.setObjectName("le_db_host")
        self.le_db_host.setPlaceholderText("localhost")
        self.le_db_login = QtWidgets.QLineEdit(dialog_db_connection)
        self.le_db_login.setGeometry(QtCore.QRect(20, 130, 281, 20))
        self.le_db_login.setObjectName("le_db_login")
        self.le_db_password = QtWidgets.QLineEdit(dialog_db_connection)
        self.le_db_password.setGeometry(QtCore.QRect(20, 180, 281, 20))
        self.le_db_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.le_db_password.setObjectName("le_db_password")
        self.label_host = QtWidgets.QLabel(dialog_db_connection)
        self.label_host.setGeometry(QtCore.QRect(20, 10, 281, 16))
        self.label_host.setObjectName("label_host")
        self.label_login = QtWidgets.QLabel(dialog_db_connection)
        self.label_login.setGeometry(QtCore.QRect(20, 110, 281, 16))
        self.label_login.setObjectName("label_login")
        self.label_password = QtWidgets.QLabel(dialog_db_connection)
        self.label_password.setGeometry(QtCore.QRect(20, 160, 281, 16))
        self.label_password.setObjectName("label_password")
        self.button_connect = QtWidgets.QPushButton(dialog_db_connection)
        self.button_connect.setGeometry(QtCore.QRect(70, 210, 181, 23))
        self.button_connect.setObjectName("button_connect")
        self.le_db_port = QtWidgets.QLineEdit(dialog_db_connection)
        self.le_db_port.setGeometry(QtCore.QRect(220, 80, 81, 20))
        self.le_db_port.setObjectName("le_db_port")
        self.le_db_port.setValidator(QtGui.QIntValidator(0, 65535))
        self.le_db_port.setPlaceholderText("3306")
        self.le_db_name = QtWidgets.QLineEdit(dialog_db_connection)
        self.le_db_name.setGeometry(QtCore.QRect(20, 80, 191, 20))
        self.le_db_name.setObjectName("le_db_name")
        self.label_database_name = QtWidgets.QLabel(dialog_db_connection)
        self.label_database_name.setGeometry(QtCore.QRect(20, 60, 191, 16))
        self.label_database_name.setObjectName("label_database_name")
        self.label_port = QtWidgets.QLabel(dialog_db_connection)
        self.label_port.setGeometry(QtCore.QRect(220, 60, 81, 16))
        self.label_port.setObjectName("label_port")

        self.retranslateUi(dialog_db_connection)
        QtCore.QMetaObject.connectSlotsByName(dialog_db_connection)

    def retranslateUi(self, dialog_db_connection):
        _translate = QtCore.QCoreApplication.translate
        dialog_db_connection.setWindowTitle(_translate("dialog_db_connection", "Подключение к базе"))
        self.label_host.setText(_translate("dialog_db_connection", "Адрес сервера:"))
        self.label_login.setText(_translate("dialog_db_connection", "Логин:"))
        self.label_password.setText(_translate("dialog_db_connection", "Пароль:"))
        self.button_connect.setText(_translate("dialog_db_connection", "Подключиться к базе данных"))
        self.le_db_port.setText(_translate("dialog_db_connection", "3306"))
        self.label_database_name.setText(_translate("dialog_db_connection", "База данных:"))
        self.label_port.setText(_translate("dialog_db_connection", "Порт:"))
