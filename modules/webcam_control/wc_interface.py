from abc import ABCMeta, abstractmethod


class WCInterface:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_webcam_list(self):
        pass

    @abstractmethod
    def choose_webcam(self, cam_index):
        pass

    @abstractmethod
    def take_photo(self):
        pass

    @abstractmethod
    def convert_image_to_rgb(self, image):
        pass
