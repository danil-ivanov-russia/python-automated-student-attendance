from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal


class SignalHolder(QtCore.QObject):
    status_signal = pyqtSignal(int)
    toggle_result_signal = pyqtSignal()
    no_more_classes_signal = pyqtSignal()

    def update_status(self, value):
        self.status_signal.emit(value)

    def toggle_result(self):
        self.toggle_result_signal.emit()

    def notify_no_classes(self):
        self.no_more_classes_signal.emit()


signal_holder = SignalHolder()
