# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'window_encode.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!





from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLineEdit


class cQLineEdit(QLineEdit):
    clicked = pyqtSignal()

    def __init__(self, widget):
        super().__init__(widget)

    def mousePressEvent(self, QMouseEvent):
        self.clicked.emit()

class Ui_encode_images_window(object):
    def setupUi(self, encode_images_window):
        encode_images_window.setObjectName("encode_images_window")
        encode_images_window.resize(311, 122)
        self.main_widget = QtWidgets.QWidget(encode_images_window)
        self.main_widget.setObjectName("main_widget")
        self.le_file_path = cQLineEdit(self.main_widget)
        self.le_file_path.setGeometry(QtCore.QRect(10, 40, 291, 20))
        self.le_file_path.setObjectName("le_file_path")
        self.label_choose_path = QtWidgets.QLabel(self.main_widget)
        self.label_choose_path.setGeometry(QtCore.QRect(10, 20, 121, 16))
        self.label_choose_path.setObjectName("label_choose_path")
        self.button_encode = QtWidgets.QPushButton(self.main_widget)
        self.button_encode.setGeometry(QtCore.QRect(70, 80, 171, 31))
        self.button_encode.setObjectName("button_encode")
        #encode_images_window.setCentralWidget(self.main_widget)

        self.retranslateUi(encode_images_window)
        QtCore.QMetaObject.connectSlotsByName(encode_images_window)

    def retranslateUi(self, encode_images_window):
        _translate = QtCore.QCoreApplication.translate
        encode_images_window.setWindowTitle(_translate("encode_images_window", "Кодирование лиц"))
        self.label_choose_path.setText(_translate("encode_images_window", "Выберите каталог:"))
        self.button_encode.setText(_translate("encode_images_window", "Закодировать данные"))
