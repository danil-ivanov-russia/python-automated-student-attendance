import cv2
from modules.webcam_control.wc_interface import WCInterface


class WebcamControl(WCInterface):

    def __init__(self):
        self.webcam_capture = None

    # Получение списка доступных веб-камер
    def get_webcam_list(self):
        cam_index = 0
        cameras = []
        while True:
            test_capture = cv2.VideoCapture(cam_index)
            if not test_capture.read()[0]:
                break
            else:
                cameras.append(cam_index)
            test_capture.release()
            cam_index += 1
        return cameras

    # Выбор активной веб-камеры
    def choose_webcam(self, cam_index):
        if self.webcam_capture is not None:
            self.webcam_capture.release()
        self.webcam_capture = cv2.VideoCapture(cam_index)

    # Создание фотографии
    def take_photo(self):
        try:
            photo = self.webcam_capture.read()[1]
            return photo
        except Exception as e:
            self.webcam_capture.release()
            print("Exception occurred: ", e)
            return None

    # Перевод фотографии в формат RGB
    def convert_image_to_rgb(self, image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
