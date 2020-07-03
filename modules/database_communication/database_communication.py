import pymysql
import io
import numpy as np
from cryptography.fernet import Fernet
from modules.database_communication.db_interface import DBInterface
import constants


class DatabaseCommunication(DBInterface):

    # Инициализация переменной соединения с базой
    def __init__(self):
        self.connection = None

    # Перевод массива параметров лица в двоичный вид для хранения в базе
    def encoding_to_blob(self, encoding):
        out = io.BytesIO()
        np.save(out, encoding)
        out.seek(0)
        return out.read()

    # Перевод параметров лица из двоичного вида в массив при полученнии данных из базы
    def blob_to_encoding(self, blob):
        out = io.BytesIO(blob)
        out.seek(0)
        return np.load(out)

    # Шифрование строки шифром Fernet и перевод в двоичный вид
    def encrypt_string_to_blob(self, string):
        key = constants.ENCRYPTION_KEY
        f = Fernet(key)
        encrypted_blob = f.encrypt(string.encode('utf-8'))
        return encrypted_blob

    # Дешифрование двоичного объекта шифром Fernet и перевод в строку
    def decrypt_blob_to_string(self, blob):
        key = constants.ENCRYPTION_KEY
        f = Fernet(key)
        decrypted_string = f.decrypt(blob).decode('utf-8')
        return decrypted_string

    # Подключение к базе данных
    def connect_to_database(self, login, password, host="localhost", db=None, port=3306):
        try:
            self.connection = pymysql.connect(host=host,
                                              user=login,
                                              password=password,
                                              db=db,
                                              port=port,
                                              charset='utf8mb4',
                                              cursorclass=pymysql.cursors.DictCursor)
            print("Connection established.")
            return True
        except Exception as e:
            self.connection = None
            print("Exception occurred: ", e)
            return False

    # Получение расписания на конкретный день недели для определённой аудитории
    def get_classes_for_today(self, classroom_id, day_of_week):
        classes_ids = []
        classes_time_start = []
        classes_time_end = []
        classes_groups = []

        try:
            with self.connection.cursor() as cursor:

                sql = "SELECT class.id, class.time_start, class.time_end, class_group.group_id " \
                      "FROM class " \
                      "LEFT JOIN class_group on class.id = class_group.class_id " \
                      "WHERE class.classroom_id = %s AND class.day_of_week = %s " \
                      "ORDER BY time_start;"
                cursor.execute(sql, (classroom_id, day_of_week))
                record = cursor.fetchall()
                for class_item in record:
                    classes_ids.append(class_item.get("id"))
                    classes_time_start.append(class_item.get("time_start"))
                    classes_time_end.append(class_item.get("time_end"))
                    classes_groups.append(class_item.get("group_id"))

        except Exception as e:
            print("Exception occurred: ", e)

        return classes_ids, classes_time_start, classes_time_end, classes_groups

    # Получение списка студентов каждой группы по списку требуемых групп
    def get_students_by_groups(self, group_ids):
        student_ids = []
        student_names = []
        group_names = []
        face_encodings = []
        try:
            with self.connection.cursor() as cursor:
                for group_id in group_ids:
                    sql = "SELECT student.id, student.first_name, " \
                          "student.last_name, " \
                          "student.patronym, " \
                          "`group`.group_name, face_encoding.encoding " \
                          "FROM student " \
                          "LEFT JOIN face_encoding on student.id = face_encoding.student_id " \
                          "LEFT JOIN `group` on student.group_id = `group`.id " \
                          "WHERE student.group_id = %s;"
                    cursor.execute(sql, (group_id,))
                    record = cursor.fetchall()
                    for student in record:
                        student_ids.append(student.get("id"))
                        student_name = self.decrypt_blob_to_string(student.get("last_name")) \
                                       + " " \
                                       + self.decrypt_blob_to_string(student.get("first_name"))
                        if student.get("patronym") is not None:
                            student_name = student_name + " " \
                                           + self.decrypt_blob_to_string(student.get("patronym"))
                        student_names.append(student_name)
                        group_names.append(student.get("group_name"))
                        face_encodings.append(self.blob_to_encoding(student.get("encoding")))

        except Exception as e:
            print("Exception occurred: ", e)

        return student_ids, student_names, group_names, face_encodings

    # Фиксирование отсутствия указанных студентов на конкретном занятии, проведённым сегодня
    def mark_non_attendance(self, student_ids, class_id, class_date, record_time):
        try:
            with self.connection.cursor() as cursor:
                for student_id in student_ids:
                    sql = "INSERT INTO " \
                          "`student_non_attendance` (student_id, class_id, class_date, record_time) " \
                          "VALUES " \
                          "(%s, %s, %s, %s);"
                    cursor.execute(sql, (student_id, class_id, class_date, record_time))
                self.connection.commit()
        except Exception as e:
            print("Exception occurred: ", e)

    # Получение списка всех аудиторий
    def get_all_classrooms(self):
        classrooms_ids = []
        classrooms_names = []
        try:
            with self.connection.cursor() as cursor:

                cursor.execute("""SELECT * 
                                FROM classroom 
                                ORDER BY room_name;
                                """)

                record = cursor.fetchall()
                for classroom in record:
                    classrooms_ids.append(classroom.get("id"))
                    classrooms_names.append(classroom.get("room_name"))

        except Exception as e:
            print("Exception occurred: ", e)

        return classrooms_ids, classrooms_names

    # def test_database_creation():
    #     try:
    #         with connection.cursor() as cursor:
    #             pass
    #             # query = "INSERT INTO " \
    #             #         "`group` (`group_name`) " \
    #             #         "VALUES " \
    #             #         "('КТбо4-1'), ('КТбо4-2'), ('КТбо4-3'), ('КТбо4-4'), ('КТбо4-5'), ('КТбо4-6');"
    #             # query = "INSERT INTO " \
    #             #          "`classroom` (`room_name`) " \
    #             #          "VALUES " \
    #             #          "('Г-401'), ('Г-425'), ('Г-409'), ('Г-301');"
    #             # cursor.execute(query)
    #             # query = "INSERT INTO " \
    #             #         "`class` (`classroom_id`, `group_id`, `time_start`, `time_end`, `day_of_week`) " \
    #             #         "VALUES " \
    #             #         "(17, 1, 095000, 112500, 6), " \
    #             #         "(17, 2, 095000, 112500, 6), " \
    #             #         "(17, 3, 095000, 112500, 6), " \
    #             #         "(18, 5, 095000, 112500, 6), " \
    #             #         "(18, 6, 095000, 112500, 6), " \
    #             #         "(18, 2, 115500, 133000, 6), " \
    #             #         "(20, 1, 115500, 133000, 6), " \
    #             #         "(20, 4, 115500, 133000, 6);"
    #             # cursor.execute(query)
    #             # query = "INSERT INTO " \
    #             #         "`student` (`first_name`, `last_name`, `patronym`, `group_id`) " \
    #             #         "VALUES " \
    #             #         "(%s, %s, %s, %s);"
    #             # cursor.execute(query, ("Danil", "Ivanov", "Aleksandrovich", 1))
    #             # cursor.execute(query, ("Billy", "Boyd", None, 1))
    #             # cursor.execute(query, ("Dominic", "Monaghan", None, 2))
    #             # cursor.execute(query, ("Elijah", "Wood", None, 2))
    #             # cursor.execute(query, ("Ian", "McKellen", None, 3))
    #             # cursor.execute(query, ("Liv", "Tyler", None, 3))
    #             # cursor.execute(query, ("Orlando", "Bloom", None, 4))
    #             # cursor.execute(query, ("Peter", "Jackson", None, 4))
    #             # cursor.execute(query, ("Sean", "Astin", None, 5))
    #             # cursor.execute(query, ("Sean", "Bean", None, 5))
    #             # cursor.execute(query, ("Viggo", "Mortensen", None, 6))
    #             # query = "INSERT INTO " \
    #             #         "`face_encoding` (`student_id`, `encoding`) " \
    #             #         "VALUES " \
    #             #         "(%s, %s);"
    #             # cursor.execute(query, (1, encoding_to_blob(fr.encode_face('TestFaceDirectory/danil-1.jpg'))))
    #             # cursor.execute(query, (1, encoding_to_blob(fr.encode_face('TestFaceDirectory/danil-2.jpg'))))
    #             # cursor.execute(query, (1, encoding_to_blob(fr.encode_face('TestFaceDirectory/danil-3.jpg'))))
    #             # cursor.execute(query, (1, encoding_to_blob(fr.encode_face('TestFaceDirectory/danil-4.jpg'))))
    #             # cursor.execute(query, (2, encoding_to_blob(fr.encode_face('TestFaceDirectory/billy-boyd-1.jpg'))))
    #             # cursor.execute(query, (2, encoding_to_blob(fr.encode_face('TestFaceDirectory/billy-boyd-3.jpg'))))
    #             # cursor.execute(query, (2, encoding_to_blob(fr.encode_face('TestFaceDirectory/billy-boyd-4.jpg'))))
    #             # cursor.execute(query, (2, encoding_to_blob(fr.encode_face('TestFaceDirectory/billy-boyd-7.jpg'))))
    #             # cursor.execute(query, (3, encoding_to_blob(fr.encode_face('TestFaceDirectory/dominic-monaghan-3.jpg'))))
    #             # cursor.execute(query, (3, encoding_to_blob(fr.encode_face('TestFaceDirectory/dominic-monaghan-5.jpg'))))
    #             # cursor.execute(query, (3, encoding_to_blob(fr.encode_face('TestFaceDirectory/dominic-monaghan-7.jpg'))))
    #             # cursor.execute(query, (3, encoding_to_blob(fr.encode_face('TestFaceDirectory/dominic-monaghan-9.jpg'))))
    #             # cursor.execute(query, (4, encoding_to_blob(fr.encode_face('TestFaceDirectory/elijah-wood-1.jpg'))))
    #             # cursor.execute(query, (4, encoding_to_blob(fr.encode_face('TestFaceDirectory/elijah-wood-2.jpg'))))
    #             # cursor.execute(query, (4, encoding_to_blob(fr.encode_face('TestFaceDirectory/elijah-wood-3.jpg'))))
    #             # cursor.execute(query, (4, encoding_to_blob(fr.encode_face('TestFaceDirectory/elijah-wood-4.jpg'))))
    #             # cursor.execute(query, (5, encoding_to_blob(fr.encode_face('TestFaceDirectory/ian-mckellen-1.jpg'))))
    #             # cursor.execute(query, (5, encoding_to_blob(fr.encode_face('TestFaceDirectory/ian-mckellen-2.jpg'))))
    #             # cursor.execute(query, (5, encoding_to_blob(fr.encode_face('TestFaceDirectory/ian-mckellen-3.jpg'))))
    #             # cursor.execute(query, (5, encoding_to_blob(fr.encode_face('TestFaceDirectory/ian-mckellen-4.jpg'))))
    #             # cursor.execute(query, (6, encoding_to_blob(fr.encode_face('TestFaceDirectory/liv-tyler-1.jpg'))))
    #             # cursor.execute(query, (6, encoding_to_blob(fr.encode_face('TestFaceDirectory/liv-tyler-2.jpg'))))
    #             # cursor.execute(query, (6, encoding_to_blob(fr.encode_face('TestFaceDirectory/liv-tyler-3.jpg'))))
    #             # cursor.execute(query, (6, encoding_to_blob(fr.encode_face('TestFaceDirectory/liv-tyler-4.jpg'))))
    #             # cursor.execute(query, (7, encoding_to_blob(fr.encode_face('TestFaceDirectory/orlando-bloom-1.jpg'))))
    #             # cursor.execute(query, (7, encoding_to_blob(fr.encode_face('TestFaceDirectory/orlando-bloom-2.jpg'))))
    #             # cursor.execute(query, (7, encoding_to_blob(fr.encode_face('TestFaceDirectory/orlando-bloom-3.jpg'))))
    #             # cursor.execute(query, (7, encoding_to_blob(fr.encode_face('TestFaceDirectory/orlando-bloom-4.jpg'))))
    #             # cursor.execute(query, (8, encoding_to_blob(fr.encode_face('TestFaceDirectory/peter-jackson-3.jpg'))))
    #             # cursor.execute(query, (8, encoding_to_blob(fr.encode_face('TestFaceDirectory/peter-jackson-4.jpg'))))
    #             # cursor.execute(query, (8, encoding_to_blob(fr.encode_face('TestFaceDirectory/peter-jackson-5.jpg'))))
    #             # cursor.execute(query, (8, encoding_to_blob(fr.encode_face('TestFaceDirectory/peter-jackson-6.jpg'))))
    #             # cursor.execute(query, (9, encoding_to_blob(fr.encode_face('TestFaceDirectory/sean-astin-1.jpg'))))
    #             # cursor.execute(query, (9, encoding_to_blob(fr.encode_face('TestFaceDirectory/sean-astin-2.jpg'))))
    #             # cursor.execute(query, (9, encoding_to_blob(fr.encode_face('TestFaceDirectory/sean-astin-3.jpg'))))
    #             # cursor.execute(query, (9, encoding_to_blob(fr.encode_face('TestFaceDirectory/sean-astin-5.jpg'))))
    #             # cursor.execute(query, (10, encoding_to_blob(fr.encode_face('TestFaceDirectory/sean-bean-1.jpg'))))
    #             # cursor.execute(query, (10, encoding_to_blob(fr.encode_face('TestFaceDirectory/sean-bean-2.jpg'))))
    #             # cursor.execute(query, (10, encoding_to_blob(fr.encode_face('TestFaceDirectory/sean-bean-4.jpg'))))
    #             # cursor.execute(query, (10, encoding_to_blob(fr.encode_face('TestFaceDirectory/sean-bean-5.jpg'))))
    #             # cursor.execute(query, (11, encoding_to_blob(fr.encode_face('TestFaceDirectory/viggo-mortensen-1.jpg'))))
    #             # cursor.execute(query, (11, encoding_to_blob(fr.encode_face('TestFaceDirectory/viggo-mortensen-2.jpg'))))
    #             # cursor.execute(query, (11, encoding_to_blob(fr.encode_face('TestFaceDirectory/viggo-mortensen-3.jpg'))))
    #             # cursor.execute(query, (11, encoding_to_blob(fr.encode_face('TestFaceDirectory/viggo-mortensen-7.jpg'))))
    #
    #
    #         connection.commit()
    #
    #         with connection.cursor() as cursor:
    #             # Read a single record
    #             sql = "SELECT * FROM `group`;"
    #             cursor.execute(sql)
    #             result = cursor.fetchall()
    #             print(result)
    #     except Exception as e:
    #         print("Exception occurred: ", e)
    #     finally:
    #         connection.close()
    #     pass
