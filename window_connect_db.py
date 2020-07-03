from PyQt5 import QtWidgets, QtCore

from UI.dialog_bd_connection import Ui_dialog_db_connection

from modules.database_communication.db_interface import DBInterface


class WindowConnectDB(QtWidgets.QDialog):

    def __init__(self, db: DBInterface):
        QtWidgets.QWidget.__init__(self)

        self.ui = Ui_dialog_db_connection()

        self.ui.setupUi(self)

        self.setFixedSize(self.size())

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.ui.button_connect.clicked.connect(self.connect_to_db)

        self.db: DBInterface = db

    def connect_to_db(self):
        connection_result = self.db.connect_to_database(self.ui.le_db_login.text(),
                                                        self.ui.le_db_password.text(),
                                                        self.ui.le_db_host.text(),
                                                        self.ui.le_db_name.text(),
                                                        int(self.ui.le_db_port.text()))
        if connection_result:
            self.accept()
        else:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', "Введены некорректные данные.")
