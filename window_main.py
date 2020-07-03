from enum import Enum
import datetime
import pickle
import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
from UI.main_window import Ui_main_window
from window_connect_db import WindowConnectDB
import signal_controller as sc
import images_qr

from modules.database_communication.db_interface import DBInterface
from modules.database_communication.database_communication import DatabaseCommunication

from modules.webcam_control.wc_interface import WCInterface
from modules.webcam_control.webcam_control import WebcamControl

from modules.attendance_control.ac_interface import ACInterface
from modules.attendance_control.attendance_control import AttendanceControl

from modules.face_detection.fd_interface import FDInterface
from modules.face_detection.face_detection import FaceDetection

import sys


# Перечисление выводимых состояний системы
class ProgramStatus(Enum):
    NOT_WORKING = "Отключено"
    IDLE = "Ожидание занятия"
    RECORDING = "Запись занятия"


# Поток непрерывного получения изображения с веб-камеры
class WebcamThread(QtCore.QThread):
    update_signal = pyqtSignal(QtGui.QImage)

    def __init__(self, webcam_control: WCInterface):
        super().__init__()
        self.wc = webcam_control

    def run(self):
        while True:
            image = self.wc.take_photo()
            if image is not None:
                image_rgb = self.wc.convert_image_to_rgb(image)
                height, width, channel = image_rgb.shape
                bytes_per_line = channel * width
                image_qt = QtGui.QImage(image_rgb.data,
                                        width,
                                        height,
                                        bytes_per_line,
                                        QtGui.QImage.Format_RGB888)
                image_qt_resized = image_qt.scaled(640, 360, QtCore.Qt.KeepAspectRatio)
                self.update_signal.emit(image_qt_resized)


# Поток, в котором осуществляется контроль посещаемости
class AttendanceControlThread(QtCore.QThread):
    change_status_signal = pyqtSignal(int)

    def __init__(self, attendance_control: ACInterface):
        super().__init__()
        self.ac = attendance_control

    def run(self):
        self.ac.start_class_attendance_detection()


# Реализация главного окна системы
class WindowMain(QtWidgets.QMainWindow):

    def __init__(self, db: DBInterface, wc: WCInterface, ac: ACInterface):
        QtWidgets.QWidget.__init__(self)

        self.ui = Ui_main_window()

        self.ui.setupUi(self)

        self.setFixedSize(self.size())

        self.ui.button_refresh_camera_list.clicked.connect(self.fill_camera_combo_box)

        self.ui.cb_camera_list.currentIndexChanged.connect(self.choose_camera_from_combo_box)

        self.ui.button_confirm_classroom.clicked.connect(self.confirm_classroom_choice)

        self.ui.button_toggle_recording.clicked.connect(self.start_recording)
        self.ui.button_confirm_attendance.clicked.connect(self.confirm_attendance)

        self.ui.sb_percentage.setValue(67.0)
        self.ui.sb_percentage.valueChanged.connect(self.compare_attendance_percentage)

        self.set_result_table()

        self.ui.cb_choose_records.currentTextChanged.connect(self.change_table_records)

        self.db: DBInterface = db
        self.wc: WCInterface = wc
        self.ac: ACInterface = ac

        self.attendance_records_list = self.get_records_from_file()
        self.fill_records_combo_box()

    # Переопределение базового метода закрытия окна
    def closeEvent(self, event):
        self.update_records_file(self.attendance_records_list)
        if not self.attendance_records_list:
            event.accept()
        else:
            warning_text = "Остались неподтверждённые отчёты. Вы точно хотите закрыть программу?"
            confirmation = QtWidgets.QMessageBox.question(self, "Предупреждение", warning_text,
                                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if confirmation == QtWidgets.QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

    # Получение списка неподтверждённых отчётов из файла
    def get_records_from_file(self):
        if os.path.isfile('records.pickle'):
            with open('records.pickle', 'rb') as f:
                attendance_records_list = pickle.load(f)
            return attendance_records_list
        else:
            return []

    # Заполнение списка отчётов
    def fill_records_combo_box(self):
        self.ui.cb_choose_records.clear()
        if not self.attendance_records_list:
            self.ui.cb_choose_records.setEnabled(False)
            self.ui.button_confirm_attendance.setEnabled(False)
        else:
            self.ui.cb_choose_records.setEnabled(True)
            self.ui.button_confirm_attendance.setEnabled(True)
            for i in range(len(self.attendance_records_list)):
                current_record_name = "Занятие от " + str(self.attendance_records_list[i].date) + ", " \
                                      + self.attendance_records_list[i].time.strftime('%H:%M:%S')
                self.ui.cb_choose_records.addItem(current_record_name, self.attendance_records_list[i])

    # Обновление файла неподтверждённых отчетов
    def update_records_file(self, new_attendance_records_list):
        with open('records.pickle', 'wb') as f:
            pickle.dump(new_attendance_records_list, f)

    # Вспомогательный класс для хранения информации об отчётах
    class AttendanceRecord:
        def __init__(self, attendance_records, class_id, date, time):
            self.attendance_records = attendance_records
            self.class_id = class_id
            self.date = date
            self.time = time

    # Подготовка результатов контроля посещаемости
    def ready_results(self):
        attendance_records = self.ac.get_attendance_records()
        new_attendance_record = self.AttendanceRecord(attendance_records,
                                                      self.ac.get_last_ended_class_id(),
                                                      datetime.date.today(),
                                                      datetime.datetime.now().time())
        self.attendance_records_list.insert(0, new_attendance_record)
        self.fill_records_combo_box()
        self.compare_attendance_percentage()
        if self.ui.cb_automatic_confirmation.checkState() == 0:
            QtWidgets.QMessageBox.information(self, 'Сообщение', "Отчёт о посещаемости готов.")
        else:
            self.send_attendance_to_database()

    # Изменение текущего выбранного отчёта
    def change_table_records(self):
        attendance_record = self.ui.cb_choose_records.itemData(self.ui.cb_choose_records.currentIndex())
        self.output_result_to_table(attendance_record)

    # Вывод сообщения об отсутствии занятий на сегодня
    def notify_attendance_end(self):
        QtWidgets.QMessageBox.information(self, 'Сообщение', "Больше занятий на сегодня нет.")

    # Подтверждение выбранного отчёта о посещаемости
    def confirm_attendance(self):
        question_text = "Вы точно хотите подтвердить данные о посещении?"
        confirmation = QtWidgets.QMessageBox.question(self, "Подтверждение", question_text,
                                                      QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if confirmation == QtWidgets.QMessageBox.Yes:
            self.send_attendance_to_database()

    # Передача данных о посещаемости в базу
    def send_attendance_to_database(self):
        student_ids = []
        for i in range(self.ui.table_attendance_result.rowCount()):
            if self.ui.table_attendance_result.item(i, 4).checkState() == 0:
                student_ids.append(int(self.ui.table_attendance_result.item(i, 0).text()))
        attendance_record = self.ui.cb_choose_records.itemData(self.ui.cb_choose_records.currentIndex())
        self.db.mark_non_attendance(student_ids,
                                    attendance_record.class_id,
                                    attendance_record.date,
                                    attendance_record.time)
        self.attendance_records_list.remove(attendance_record)
        self.update_records_file(self.attendance_records_list)
        QtWidgets.QMessageBox.information(self, 'Сообщение', "Посещаемость занятия зафиксирована.")
        self.fill_records_combo_box()

    # Настройка таблицы отчёта посещаемости
    def set_result_table(self):
        self.ui.table_attendance_result.setColumnCount(5)
        self.ui.table_attendance_result.setHorizontalHeaderLabels(["ID", "ФИО студента", "Группа",
                                                                   "Процент обнаружения", "Присутствие"])
        self.ui.table_attendance_result.setColumnWidth(0, 40)
        self.ui.table_attendance_result.setColumnWidth(1, 282)
        self.ui.table_attendance_result.setColumnWidth(2, 80)
        self.ui.table_attendance_result.setColumnWidth(3, 138)
        self.ui.table_attendance_result.setColumnWidth(4, 80)

        self.ui.table_attendance_result.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        self.ui.table_attendance_result.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self.ui.table_attendance_result.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)
        self.ui.table_attendance_result.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)
        self.ui.table_attendance_result.horizontalHeader().setStretchLastSection(True)

        self.ui.table_attendance_result.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.table_attendance_result.verticalHeader().hide()
        self.ui.table_attendance_result.itemClicked.connect(self.save_record_changes)
        self.ui.table_attendance_result.setSortingEnabled(True)

    # Отключение взаимодействия с элементами интерфейса во время записи занятия
    def disable_interaction(self):
        self.ui.cb_camera_list.setEnabled(False)
        self.ui.button_refresh_camera_list.setEnabled(False)
        self.ui.button_toggle_recording.setEnabled(False)

    # Включение взаимодействия с элементами интерфейса после записи занятия
    def enable_interaction(self):
        self.ui.cb_camera_list.setEnabled(True)
        self.ui.button_refresh_camera_list.setEnabled(True)
        self.ui.button_toggle_recording.setEnabled(True)

    # Вспомогательный класс ячеек с численными значениями, которые можно сортировать по возрастанию и убыванию
    class NumericTableWidgetItem(QtWidgets.QTableWidgetItem):
        def __init__(self, value):
            super().__init__(str(value))
            self.value = value

        def __lt__(self, other):
            return self.value < other.value

    # Вывод отчёта в таблицу
    def output_result_to_table(self, attendance_record):
        if attendance_record is None:
            self.ui.table_attendance_result.setRowCount(0)
        else:
            attendance_records = attendance_record.attendance_records
            self.ui.label_current_date.setText(str(attendance_record.date))
            self.ui.label_current_time.setText(attendance_record.time.strftime('%H:%M:%S'))
            self.ui.table_attendance_result.setRowCount(0)
            self.ui.table_attendance_result.setRowCount(len(attendance_records))
            for i in range(len(attendance_records)):
                self.ui.table_attendance_result.setItem(i,
                                                        0,
                                                        self.NumericTableWidgetItem(
                                                            attendance_records[i].student.id))
                self.ui.table_attendance_result.setItem(i,
                                                        1,
                                                        QtWidgets.QTableWidgetItem(
                                                            attendance_records[i].student.full_name))
                self.ui.table_attendance_result.setItem(i,
                                                        2,
                                                        QtWidgets.QTableWidgetItem(
                                                            attendance_records[i].student.group_name))
                self.ui.table_attendance_result.setItem(i,
                                                        3,
                                                        self.NumericTableWidgetItem(
                                                            attendance_records[i].percentage))
                checkbox_attendance = QtWidgets.QTableWidgetItem()
                checkbox_attendance.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                self.ui.table_attendance_result.setItem(i,
                                                        4,
                                                        checkbox_attendance)
                if attendance_records[i].attendance != 0:
                    self.ui.table_attendance_result.item(i, 4).setCheckState(QtCore.Qt.Checked)
                else:
                    self.ui.table_attendance_result.item(i, 4).setCheckState(QtCore.Qt.Unchecked)

    # Установка флажков посещения текущего отчёта в зависимости от процента
    def compare_attendance_percentage(self):
        for i in range(self.ui.table_attendance_result.rowCount()):
            percentage = self.ui.table_attendance_result.item(i, 3).text()
            if float(percentage) >= self.ui.sb_percentage.value():
                self.ui.table_attendance_result.item(i, 4).setCheckState(QtCore.Qt.Checked)
            else:
                self.ui.table_attendance_result.item(i, 4).setCheckState(QtCore.Qt.Unchecked)

    # Сохранение правок текущего отчёта
    def save_record_changes(self, item):
        if item.column() == 4:
            student_ids = []
            for i in range(self.ui.table_attendance_result.rowCount()):
                if self.ui.table_attendance_result.item(i, 4).checkState() == 0:
                    student_ids.append(int(self.ui.table_attendance_result.item(i, 0).text()))

            current_attendance_record = self.ui.cb_choose_records.itemData(self.ui.cb_choose_records.currentIndex())
            for record in current_attendance_record.attendance_records:
                if record.student.id in student_ids:
                    record.attendance = 0
                else:
                    record.attendance = 1
            self.attendance_records_list = [current_attendance_record if record == current_attendance_record
                                            else record for record in self.attendance_records_list]
            self.update_records_file(self.attendance_records_list)

    # Запуск контроля посещаемости
    def start_recording(self):
        if self.ui.cb_camera_list.isEnabled() and not self.ui.button_confirm_classroom.isEnabled():
            self.disable_interaction()
            self.attendance_thread = AttendanceControlThread(self.ac)
            self.set_new_status(1)
            self.attendance_thread.start()
        elif not self.ui.cb_camera_list.isEnabled():
            QtWidgets.QMessageBox.critical(self, 'Ошибка', "Необходимо наличие рабочей камеры.")
        else:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', "Необходимо подтвердить выбор аудитории.")

    # Создание диалога подключения к базе
    def start_connect_dialog(self):
        connect_dialog = WindowConnectDB(self.db)
        if connect_dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.configure_window()
            self.show()
        else:
            sys.exit()

    # Заполнение списка доступных камер
    def fill_camera_combo_box(self):
        self.ui.cb_camera_list.setEnabled(False)
        self.ui.button_refresh_camera_list.setEnabled(False)
        self.ui.label_camera_output.setPixmap(QtGui.QPixmap(":/resources/cam_loading.png"))
        self.ui.cb_camera_list.clear()
        camera_list = ["Камера " + str(number) for number in self.wc.get_webcam_list()]
        self.ui.cb_camera_list.addItems(camera_list)
        if not camera_list:
            self.ui.label_camera_output.setPixmap(QtGui.QPixmap(":/resources/cam_no_feed.png"))
        else:
            self.ui.cb_camera_list.setEnabled(True)
        self.ui.button_refresh_camera_list.setEnabled(True)

    # Выбор камеры из списка
    def choose_camera_from_combo_box(self):
        current_camera = self.ui.cb_camera_list.currentIndex()
        self.wc.choose_webcam(current_camera)
        self.ui.label_camera_output.setPixmap(QtGui.QPixmap(":/resources/cam_loading.png"))

    # Отображение изображения с камеры
    def set_camera_output(self, image):
        self.ui.label_camera_output.setPixmap(QtGui.QPixmap.fromImage(image))

    # Заполнение списка аудиторий
    def fill_classroom_combo_box(self):
        self.ui.cb_choose_classroom.clear()
        classroom_ids, classroom_names = self.db.get_all_classrooms()
        if not classroom_names:
            self.ui.cb_choose_classroom.setEnabled(False)
        else:
            completer = QtWidgets.QCompleter(classroom_names)
            for i in range(len(classroom_names)):
                self.ui.cb_choose_classroom.addItem(classroom_names[i], classroom_ids[i])
            self.ui.cb_choose_classroom.setCompleter(completer)
            self.ui.cb_choose_classroom.setCurrentText("")

    # Подтверждение выбора аудитории
    def confirm_classroom_choice(self):
        all_classrooms = [self.ui.cb_choose_classroom.itemText(i) for i in range(self.ui.cb_choose_classroom.count())]
        current_classroom = self.ui.cb_choose_classroom.currentText()
        if current_classroom in all_classrooms:
            question_text = "Вы точно хотите выбрать аудиторию {}?".format(current_classroom)
            confirmation = QtWidgets.QMessageBox.question(self, "Подтверждение", question_text,
                                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if confirmation == QtWidgets.QMessageBox.Yes:
                self.fill_classes_for_today()
                self.ui.cb_choose_classroom.setEnabled(False)
                self.ui.button_confirm_classroom.setEnabled(False)
        else:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', "Аудитории с таким названием не существует.")

    # Получение расписания занятий на сегодня
    def fill_classes_for_today(self):
        classroom_id = self.ui.cb_choose_classroom.itemData(self.ui.cb_choose_classroom.currentIndex())
        classes_ids, classes_time_start, classes_time_end, classes_groups \
            = self.db.get_classes_for_today(classroom_id, datetime.datetime.today().weekday())

        self.ac.set_today_classes(self.ac.merge_groups_by_class(classes_ids,
                                                                classes_time_start,
                                                                classes_time_end,
                                                                classes_groups))
        self.set_new_status(0)

    # Настройка главного окна и создание потоков
    def configure_window(self):
        self.set_new_status(0)
        self.fill_camera_combo_box()
        self.fill_classroom_combo_box()

        sc.signal_holder.status_signal.connect(self.set_new_status)

        sc.signal_holder.toggle_result_signal.connect(self.ready_results)

        sc.signal_holder.no_more_classes_signal.connect(self.notify_attendance_end)

        self.webcam_thread = WebcamThread(self.wc)
        self.webcam_thread.update_signal.connect(self.set_camera_output)
        self.webcam_thread.start()

    # Отображение статуса системы
    def set_new_status(self, value):
        status_text = {
            0: ProgramStatus.NOT_WORKING.value,
            1: ProgramStatus.IDLE.value,
            2: ProgramStatus.RECORDING.value
        }[value]
        if value == 0:
            self.enable_interaction()
        self.ui.label_status_current.setText(status_text)


# Главная функция системы
def main():
    app = QtWidgets.QApplication([])

    translator = QtCore.QTranslator(app)
    locale = QtCore.QLocale.system().name()
    path = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath)
    translator.load('qtbase_%s' % locale, path)
    app.installTranslator(translator)
    app.setWindowIcon(QtGui.QIcon(':/resources/icon.png'))

    database_communication: DBInterface = DatabaseCommunication()
    webcam_control: WCInterface = WebcamControl()
    face_detection: FDInterface = FaceDetection()
    attendance_control = AttendanceControl(webcam_control, face_detection, database_communication)

    window = WindowMain(database_communication, webcam_control, attendance_control)

    window.start_connect_dialog()
    sys.exit(app.exec_())
