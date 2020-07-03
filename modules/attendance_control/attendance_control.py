import datetime
import random
import sched
import time
import signal_controller as sc
from modules.attendance_control.ac_interface import ACInterface
from modules.database_communication.db_interface import DBInterface
from modules.face_detection.fd_interface import FDInterface
from modules.webcam_control.wc_interface import WCInterface


# Вспомогательный класс представления всех данных о студенте
class Student:

    def __init__(self, id, full_name, group_name):
        self.id = id
        self.full_name = full_name
        self.face_encodings = []
        self.group_name = group_name


# Вспомогательный класс представления записи посещаемости студента
class StudentAttendanceRecord:

    def __init__(self, student: Student, attendance: int):
        self.student = student
        self.attendance = attendance
        self.percentage = 0.0


# Вспомогательный класс представления аудиторного занятия
class UniversityClass:

    def __init__(self, id, time_start, time_end, ):
        self.id = id
        self.time_start = time_start
        self.time_end = time_end
        self.groups_list = []

    def get_duration(self):
        return self.time_end - self.time_start


class AttendanceControl(ACInterface):

    def __init__(self, webcam_control: WCInterface, face_detection: FDInterface, database_communication: DBInterface):
        # Подключение используемых модулей
        self.wc = webcam_control
        self.fd = face_detection
        self.db = database_communication

        # Список занятий на сегодня
        self.today_classes = []

        # ID последнего проведённого занятия
        self.last_ended_class_id = None

        # Инициализация списка записей посещаемости студентов
        self.attendance_records = []

        # Инициализация объектов планирования
        self.photo_scheduler = sched.scheduler(time.time, time.sleep)
        self.class_scheduler = sched.scheduler(time.time, time.sleep)

    # Получение списка записей посещаемости
    def get_attendance_records(self):
        return self.attendance_records

    # Получение ID последнего проведённого занятия
    def get_last_ended_class_id(self):
        return self.last_ended_class_id

    # Заполнение списка сегодняшних занятий
    def set_today_classes(self, value):
        self.today_classes = value

    # Перевод значения момента времени в значение продолжительность
    def convert_time_to_timedelta(self, time_value):
        return datetime.datetime.combine(datetime.date.min, time_value) - datetime.datetime.min

    # Перевод значения продолжительности в значение момента времени
    def convert_timedelta_to_time(self, timedelta_value):
        return (datetime.datetime.min + timedelta_value).time()

    # Формирование списка занятия со слиянием занятий, проходящих для нескольких групп
    def merge_groups_by_class(self, classes_ids, classes_time_start, classes_time_end, classes_groups):
        classes_list = []
        current_class = None
        for i in range(len(classes_time_start)):
            if current_class is not None and current_class.id != classes_ids[i]:
                classes_list.append(current_class)
                current_class = None
            if current_class is None:
                current_class = UniversityClass(classes_ids[i],
                                                classes_time_start[i],
                                                classes_time_end[i])
            current_class.groups_list.append(classes_groups[i])
        classes_list.append(current_class)
        return classes_list

    # Формирование списка студентов
    def merge_encodings_by_student(self, student_ids, student_names, student_groups, face_encodings):
        student_list = []
        current_student = None
        for i in range(len(face_encodings)):
            if current_student is not None and current_student.id != student_ids[i]:
                student_list.append(current_student)
                current_student = None
            if current_student is None:
                current_student = Student(student_ids[i],
                                          student_names[i],
                                          student_groups[i])
            current_student.face_encodings.append(face_encodings[i])
        student_list.append(current_student)
        return student_list

    # Формирование списка записей посещаемости
    def form_attendance_records(self, student_list):
        self.attendance_records = []
        for student in student_list:
            self.attendance_records.append(StudentAttendanceRecord(student, 0))

    # Отмечание однократного наличия студентов в записях посещаемости
    def check_attendance(self, student_ids):
        for record in self.attendance_records:
            if record.student.id in student_ids:
                record.attendance += 1
                break

    # Подсчёт финального процента посещаемости для каждой записи
    def calculate_final_attendance(self, number_of_checks):
        if number_of_checks > 0:
            for record in self.attendance_records:
                record.percentage = 100 * float(record.attendance) / float(number_of_checks)

    # Вычисление случайных временных интервалов съёмки для занятия
    def determine_time_intervals(self, duration):
        intervals_list = []
        number_of_intervals = int((duration / 5.0).total_seconds() / 60)
        interval_buffer = 300.0
        for i in range(number_of_intervals - 3):
            random_number = random.randint(60, 240)
            current_interval = random_number + interval_buffer
            if i == (int((number_of_intervals - 2) / 2)):
                current_interval += 300.0
            interval_buffer = 300.0 - random_number
            intervals_list.append(float(current_interval))
            #intervals_list.append(float(2))
        return intervals_list

    # Контроль посещаемости одного занятия
    def control_single_class_attendance(self, university_class: UniversityClass):
        sc.signal_holder.update_status(1)
        student_ids, student_names, student_groups, face_encodings \
            = self.db.get_students_by_groups(university_class.groups_list)
        needed_students = self.merge_encodings_by_student(student_ids,
                                                          student_names,
                                                          student_groups,
                                                          face_encodings)
        self.form_attendance_records(needed_students)
        current_time = self.convert_time_to_timedelta(datetime.datetime.now().time())
        if university_class.time_start + datetime.timedelta(minutes=5) < current_time:
            university_class.time_start = current_time
        intervals_list = self.determine_time_intervals(university_class.get_duration())
        current_delay = 0
        for interval in intervals_list:
            current_delay += interval
            self.photo_scheduler.enter(current_delay,
                                       1,
                                       self.determine_current_attendance,
                                       argument=(needed_students,))
        sc.signal_holder.update_status(2)
        if intervals_list is not None:
            self.photo_scheduler.run()
        sc.signal_holder.update_status(1)
        self.calculate_final_attendance(len(intervals_list))
        self.last_ended_class_id = university_class.id
        sc.signal_holder.toggle_result()

    # Определение наличия студентов на занятии в текущий момент
    def determine_current_attendance(self, needed_students):
        photo = None
        while photo is None:
            photo = self.wc.take_photo()
        found_students_ids = self.fd.detect_faces(photo, needed_students)
        self.check_attendance(found_students_ids)

    # Запуск процесса учёта посещаемости на весь день
    def start_class_attendance_detection(self):
        if self.today_classes[0] is not None:
            current_time = self.convert_time_to_timedelta(datetime.datetime.now().time())
            for class_item in self.today_classes:
                if class_item.time_end < current_time:
                    pass
                elif class_item.time_start > current_time:
                    epoch_timestamp = datetime.datetime.combine(datetime.datetime.now().date(),
                                                                self.convert_timedelta_to_time(class_item.time_start)
                                                                ).timestamp()
                    self.photo_scheduler.enterabs(epoch_timestamp,
                                                  1,
                                                  self.control_single_class_attendance,
                                                  argument=(class_item,))
                else:
                    self.photo_scheduler.enter(1,
                                               1,
                                               self.control_single_class_attendance,
                                               argument=(class_item,))
            self.photo_scheduler.run()
        sc.signal_holder.status_signal.emit(0)
        sc.signal_holder.notify_no_classes()
