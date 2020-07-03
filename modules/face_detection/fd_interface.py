from abc import ABCMeta, abstractmethod


class FDInterface:
    __metaclass__ = ABCMeta

    @abstractmethod
    def encode_face(self, filename):
        pass

    @abstractmethod
    def detect_faces(self, image, needed_students):
        pass
