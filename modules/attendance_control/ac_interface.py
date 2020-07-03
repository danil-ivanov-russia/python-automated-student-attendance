from abc import ABCMeta, abstractmethod


class ACInterface:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_attendance_records(self):
        pass

    @abstractmethod
    def get_last_ended_class_id(self):
        pass

    @abstractmethod
    def set_today_classes(self, value):
        pass

    @abstractmethod
    def convert_time_to_timedelta(self, time_value):
        pass

    @abstractmethod
    def convert_timedelta_to_time(self, timedelta_value):
        pass

    @abstractmethod
    def merge_groups_by_class(self, classes_ids, classes_time_start, classes_time_end, classes_groups):
        pass

    @abstractmethod
    def merge_encodings_by_student(self, student_ids, student_names, student_groups, face_encodings):
        pass

    @abstractmethod
    def form_attendance_records(self, student_list):
        pass

    @abstractmethod
    def check_attendance(self, student_ids):
        pass

    @abstractmethod
    def calculate_final_attendance(self, number_of_checks):
        pass

    @abstractmethod
    def determine_time_intervals(self, duration):
        pass

    @abstractmethod
    def control_single_class_attendance(self, university_class):
        pass

    @abstractmethod
    def determine_current_attendance(self, needed_students):
        pass

    @abstractmethod
    def start_class_attendance_detection(self):
        pass
