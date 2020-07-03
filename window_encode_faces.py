from enum import Enum
import datetime
import pickle
import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLineEdit, QFileDialog

from UI.window_encode import Ui_encode_images_window
import xml.etree.ElementTree as xml
import images_qr

from modules.database_communication.db_interface import DBInterface
from modules.database_communication.database_communication import DatabaseCommunication

from modules.webcam_control.wc_interface import WCInterface
from modules.webcam_control.webcam_control import WebcamControl

from modules.attendance_control.ac_interface import ACInterface
from modules.attendance_control.attendance_control import AttendanceControl

from modules.face_detection.fd_interface import FDInterface
from modules.face_detection.face_detection import FaceDetection

import time
import sys


class WindowEncodeFaces(QtWidgets.QDialog):

    def __init__(self, db: DBInterface, fd: FDInterface):
        QtWidgets.QWidget.__init__(self)

        self.ui = Ui_encode_images_window()

        self.ui.setupUi(self)

        self.setFixedSize(self.size())

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.db: DBInterface = db
        self.fd: FDInterface = fd

        self.ui.le_file_path.clicked.connect(self.choose_filepath)
        self.ui.button_encode.clicked.connect(self.encode_faces_in_path)

        self.chosen_path = None

    def choose_filepath(self):
        self.chosen_path = str(QFileDialog.getExistingDirectory(self, "Выберите каталог с лицами"))
        print(self.chosen_path)
        self.ui.le_file_path.setText(self.chosen_path)

    class EncodedFace:

        def __init__(self, filename, encoding_list, encoding_blob):
            self.filename = filename
            self.encoding_list = encoding_list
            self.encoding_blob = encoding_blob

    def encode_faces_in_path(self):
        encodings_list = []
        if os.path.isfile(self.chosen_path):
            current_face = self.get_full_encoding(self.chosen_path)
            if current_face is not None:
                encodings_list.append(current_face)
        elif os.path.isdir(self.chosen_path):
            for filename in os.listdir(self.chosen_path):
                current_face = self.get_full_encoding(filename)
                if current_face is not None:
                    encodings_list.append(current_face)
        if not encodings_list:
            QtWidgets.QMessageBox.information(self, 'Сообщение', "Лиц не найдено.")
        else:
            filename = str(datetime.datetime.now())\
                           .replace("-", "")\
                           .replace(" ", "")\
                           .replace(":", "")\
                           .replace(".", "") + ".xml"
            self.createXML(filename, encodings_list)
            QtWidgets.QMessageBox.information(self, 'Сообщение', "Лица закодированы.")

    def get_full_encoding(self, filename):
        try:
            current_encoding = self.fd.encode_face(os.path.join(self.chosen_path, filename))
            current_blob = self.db.encoding_to_blob(current_encoding)
            current_face = self.EncodedFace(filename,
                                            current_encoding,
                                            current_blob)
            return current_face
        except Exception as e:
            print("Exception occurred: ", e)
            return None

    def createXML(self, xml_filename, list):
        """
        Создаем XML файл.
        """
        root = xml.Element("Encodings")
        for encoding in list:
            current_encoding = xml.Element("face_encoding")
            root.append(current_encoding)

            print(encoding.filename)
            filename = xml.SubElement(current_encoding, "filename")
            filename.text = encoding.filename

            print(encoding.encoding_list)
            encoding_list = xml.SubElement(current_encoding, "encoding_list")
            encoding_list.text = str(encoding.encoding_list)

            print(encoding.encoding_blob)
            encoding_blob = xml.SubElement(current_encoding, "encoding_blob")
            encoding_blob.text = str(encoding.encoding_blob)

        tree = xml.ElementTree(root)
        with open(xml_filename, "wb") as fh:
            tree.write(fh)


def main():
    app = QtWidgets.QApplication([])

    translator = QtCore.QTranslator(app)
    locale = QtCore.QLocale.system().name()
    path = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath)
    translator.load('qtbase_%s' % locale, path)
    app.installTranslator(translator)
    app.setWindowIcon(QtGui.QIcon(':/resources/icon.png'))

    database_communication: DBInterface = DatabaseCommunication()
    face_detection: FDInterface = FaceDetection()

    window = WindowEncodeFaces(database_communication, face_detection)
    sys.exit(window.exec_())
