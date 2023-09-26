
import cv2
from cv2 import dnn_superres


def upscale(input_path: str, output_path: str, model_path: str = 'models/EDSR_x2.pb'):
    """
    :param input_path: путь к изображению для апскейла
    :param output_path:  путь к выходному файлу
    :param model_path: путь к ИИ модели
    :return:
    """

    scaler = dnn_superres.DnnSuperResImpl_create()
    scaler.readModel(model_path)
    scaler.setModel("edsr", 2)
    image = cv2.imread(input_path)
    result = scaler.upsample(image)
    return cv2.imwrite(output_path, result)



def example():
    upscale('/home/fedor/Desktop/lama_300px.png', '/home/fedor/Desktop/lama_600px.png')


if __name__ == '__main__':
    example()
