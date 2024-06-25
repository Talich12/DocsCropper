import cv2
import os
import time
import math
import numpy as np

def measure_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Время выполнения функции {func.__name__}: {end_time - start_time} секунд")
        return result
    return wrapper

def get_angle(normal, vector):
    dot_product = sum(a*b for a, b in zip(normal, vector))
    norm_A = math.sqrt(sum(a*a for a in normal))
    norm_B = math.sqrt(sum(b*b for b in vector))

    angle_rad = math.acos(dot_product / (norm_A * norm_B))
    angle_deg = math.degrees(angle_rad)

    return angle_deg

def check_rotate(image, left, top):
    if not left or not top:
        return None
    if abs(left[0] - top[0]) < 100 or abs(left[1] - top[1]) < 100:
        return None
    height, width = image.shape[:2]

    top[1] = height - top[1]
    left[1] = height - left[1]

    normal = [0, top[1] - left[1]]
    vector = [top[0] - left[0], top[1] - left[1]]


    #print(normal, vector)
    #print("угол", get_angle(normal, vector))
    angle = get_angle(normal, vector)
    if angle > 20:
        return (90 - angle) * -1
    return None

def rotate(image, angle, center):
    # Получение размеров изображения
    height, width = image.shape[:2]

    # Создание матрицы поворота
    scale = 1.0
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, scale)

    # Поворот изображения с белыми границами
    rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

    # Сохранение результата
    cv2.imwrite('rotated_image_with_white_border.jpg', rotated_image)
    return rotated_image

def test(input_folder, output_folder):
    with os.scandir(input_folder) as entries:
        for entry in entries:
            if entry.is_file():
                image = find_doc(f'./{input_folder}/{entry.name}', 0)
                cv2.imwrite(f'./{output_folder}/{entry.name}', image)

def crop_image(image, size):
    height, width = image.shape[:2]

    new_width = width - size  # Убираем 10 пикселей с каждой стороны
    new_height = height - size  # Убираем 10 пикселей сверху и снизу

    return image[size//2:new_height, size//2:new_width]

def count_pixels(image, x, y, kernel_size=3, threshold=6):
    image = image[y-kernel_size:y+kernel_size, x-kernel_size:x+kernel_size]
    height, width = image.shape[:2]
    size = height * width
    white_pixel_count = cv2.countNonZero(image)
    
    if size - white_pixel_count < threshold:
        return False

    return True

@measure_execution_time
def find_doc(filename, time):
    if isinstance(filename, str):
        color_image = cv2.imread(filename)
        color_image = crop_image(color_image, 30)
    else:
        color_image = filename

    gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)


    _, binary_image = cv2.threshold(gray_image, 220, 255, cv2.THRESH_BINARY)


    height, width = binary_image.shape[:2]

    min_x = height
    min_y = width
    max_x = 0
    max_y = 0

    left = []
    top = []
    # Проход по каждому пикселю изображения слева направо по строкам
    for y in range(height):  # Перебор строк
        for x in range(width):  # Перебор столбцов
            if binary_image[y, x] == 0:
                if count_pixels(binary_image, x, y, 3, 12):
                    # Обновление минимальных координат
                    if x < min_x:
                        min_x = x
                        left = [x, y]

                    if y < min_y:
                        min_y = y
                        top = [x, y]
                    # Обновление максимальных координат
                    if x > max_x:
                        max_x = x
                        
                    if y > max_y:
                        max_y = y


    cropped_image = color_image[min_y:max_y, min_x:max_x]
    cv2.imwrite("cropped_image.jpg", cropped_image)
    cv2.imwrite("binry.jpg", binary_image)
    cv2.imwrite("color.jpg", color_image)
    
    angle = check_rotate(color_image, left, top)
    if angle and time == 0:
        center = (width//2, height//2)
        rotated_image =rotate(color_image, angle, center)
        #print() 
        cropped_image = find_doc(rotated_image, 1)
    return cropped_image

if __name__ == "__main__":
    #find_doc("./input/test6.jpg", 0)
    test("./input", "./output")