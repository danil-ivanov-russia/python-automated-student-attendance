import numpy as np
import face_recognition
from modules.face_detection.fd_interface import FDInterface


# Вспомогательный класс для хранения информации о студентах, не относящейся к параметрам лица
class StudentDataOnly:

    def __init__(self, id, full_name, group_name):
        self.id = id
        self.full_name = full_name
        self.group_name = group_name


class FaceDetection(FDInterface):

    # Кодирование данных лица и получение массива параметров
    def encode_face(self, filename):
        print("Encoding file: ", filename)
        current_image = face_recognition.load_image_file(filename)
        return face_recognition.face_encodings(current_image)[0]

    # Поиск указанных лиц на изображении и получение списка найденных лиц
    def detect_faces(self, image, needed_students):
        rgb_converted_image = image[:, :, ::-1]
        image_faces = face_recognition.face_locations(rgb_converted_image)
        image_face_encodings = face_recognition.face_encodings(rgb_converted_image, image_faces)

        found_students_ids = []

        single_face_encodings = []
        only_face_encodings = []
        for student in needed_students:
            for face_encoding in student.face_encodings:
                single_face_encodings.append(StudentDataOnly(student.id,
                                                             student.full_name,
                                                             student.group_name))
                only_face_encodings.append(face_encoding)

        for current_face_encoding in image_face_encodings:
            matches = face_recognition.compare_faces(only_face_encodings, current_face_encoding)
            face_distances = face_recognition.face_distance(only_face_encodings, current_face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                predicted_student_id = single_face_encodings[best_match_index].id
                if predicted_student_id not in found_students_ids:
                    found_students_ids.append(predicted_student_id)
        return found_students_ids
