from abc import ABCMeta, abstractmethod


class DBInterface:
    __metaclass__ = ABCMeta

    @abstractmethod
    def encoding_to_blob(self, encoding):
        pass

    @abstractmethod
    def blob_to_encoding(self, blob):
        pass

    @abstractmethod
    def encrypt_string_to_blob(self, string):
        pass

    @abstractmethod
    def decrypt_blob_to_string(self, blob):
        pass

    @abstractmethod
    def connect_to_database(self, login, password, host, db, port):
        pass

    @abstractmethod
    def get_classes_for_today(self, classroom_id, day_of_week):
        pass

    @abstractmethod
    def get_students_by_groups(self, group_ids):
        pass

    @abstractmethod
    def mark_non_attendance(self, student_ids, class_id, class_date, record_time):
        pass

    @abstractmethod
    def get_all_classrooms(self):
        pass
