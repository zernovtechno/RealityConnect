#
#██████╗░███████╗░█████╗░██╗░░░░░██╗████████╗██╗░░░██╗  ░█████╗░░█████╗░███╗░░██╗███╗░░██╗███████╗░█████╗░████████╗
#██╔══██╗██╔════╝██╔══██╗██║░░░░░██║╚══██╔══╝╚██╗░██╔╝  ██╔══██╗██╔══██╗████╗░██║████╗░██║██╔════╝██╔══██╗╚══██╔══╝
#██████╔╝█████╗░░███████║██║░░░░░██║░░░██║░░░░╚████╔╝░  ██║░░╚═╝██║░░██║██╔██╗██║██╔██╗██║█████╗░░██║░░╚═╝░░░██║░░░
#██╔══██╗██╔══╝░░██╔══██║██║░░░░░██║░░░██║░░░░░╚██╔╝░░  ██║░░██╗██║░░██║██║╚████║██║╚████║██╔══╝░░██║░░██╗░░░██║░░░
#██║░░██║███████╗██║░░██║███████╗██║░░░██║░░░░░░██║░░░  ╚█████╔╝╚█████╔╝██║░╚███║██║░╚███║███████╗╚█████╔╝░░░██║░░░
#╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝╚══════╝╚═╝░░░╚═╝░░░░░░╚═╝░░░  ░╚════╝░░╚════╝░╚═╝░░╚══╝╚═╝░░╚══╝╚══════╝░╚════╝░░░░╚═╝░░░
#
#█▀▄▀█ ▄▀█ █▀▄ █▀▀   █▄▄ █▄█   ▀█ █▀▀ █▀█ █▄ █ █▀█ █ █     ▀█ █▀█ ▀█ █▀ 
#█ ▀ █ █▀█ █▄▀ ██▄   █▄█  █    █▄ ██▄ █▀▄ █ ▀█ █▄█ ▀▄▀ ▄   █▄ █▄█ █▄ ▄█ ▄

import cv2
from PIL import Image, ImageTk
from io import BytesIO
import bettercam #fork of DXcam
import qrcode
import socket
import webbrowser
from flask import Flask, Response
import threading
import tkinter as tk
import numpy as np
import pyautogui
import time

app = Flask(__name__)
is_streaming = False
camera = None
show_fps = False  # Переменная для управления отображением FPS
prev_frame_time = 1
new_frame_time = 0
HighFPS = True

cursor_icon = \
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\x00\x00 ' + \
            b'\x08\x03\x00\x00\x00D\xa4\x8a\xc6\x00\x00\x003PLTE\x00\x00\x00' + \
            b'\x01\x02\x10\x00\x01\x0e\x02\x05\x16\x00\x01\x0f\x00\x00\x0e\x01' + \
            b'\x02\x11\x02\x04\x15\x01\x02\x12\x03\x05\x18\xff\xff\xff\xf5\xf5' + \
            b'\xf8\xe1\xe1\xe3\xd6\xd6\xd8\xe8\xe8\xea\xc2\xc2\xc9\xb3\xb4\xbc' + \
            b'\xbc\xcdR^\x00\x00\x00\ntRNS\x00\xbd\xe76\xd3\xf4\xb4M\x9e\x1aY' + \
            b'\xc1\x82\x1e\x00\x00\x00fIDAT8\xcb\xed\xcf1\x0e\x800\x0cC\xd1\x84' + \
            b'\x94\x02n\x0b\xdc\xff\xb4x\xea\x163#\xf1W?E\x8a-a\xba\xc5\xe3\x05' + \
            b'\x80B\x03\n\r\xb4 \xd0\x82@\x0b\x82)$h\x1e\x02L\xa1\x00N\x0f\r\xd0=' + \
            b'\x05\rp\x96\x82\xb6\xde\xf0-\xfd\x82{\x14\xf4\x92\x02\xeeV/\xd4\xec' + \
            b'\x84s7\x9e\x18\xc5Tu@\x83\xa3\xeca\x7f_\xef\x01\xd5h\x03\xe1\xc1\xcc' + \
            b'\xc3\xc0\x00\x00\x00\x00IEND\xaeB`\x82'

def cvimg_from_bytestring(raw_data):
    nparr = np.frombuffer(raw_data, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

def overlay_transparent(background, overlay, x, y):
    background_width = background.shape[1]
    background_height = background.shape[0]

    if x >= background_width or y >= background_height:
        return background

    h, w = overlay.shape[0], overlay.shape[1]

    if x + w > background_width:
        w = background_width - x
        overlay = overlay[:, :w]

    if y + h > background_height:
        h = background_height - y
        overlay = overlay[:h]

    if overlay.shape[2] < 4:
        overlay = np.concatenate(
            [
                overlay,
                np.ones((overlay.shape[0], overlay.shape[1], 1), dtype = overlay.dtype) * 255
            ],
            axis = 2,
        )

    overlay_image = overlay[..., :3]
    mask = overlay[..., 3:] / 255.0

    background[y:y+h, x:x+w] = (1.0 - mask) * background[y:y+h, x:x+w] + mask * overlay_image

    return background

cursor_cv2 = cvimg_from_bytestring(cursor_icon)

def generate_frames():
    global camera
    global new_frame_time
    global prev_frame_time
    while is_streaming:
            frame = camera.get_latest_frame()
            if (show_fps):
                new_frame_time = time.time()
                fps = str(1 // (new_frame_time - prev_frame_time))
                cv2.putText(frame, fps, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                prev_frame_time = new_frame_time
            cursor_x = pyautogui.position().x + 3
            cursor_y = pyautogui.position().y + 3
            if (cursor_x < frame.shape[1] and cursor_y < frame.shape[0] and cursor_x > 0 and cursor_y > 0): 
                frame = overlay_transparent(frame, cursor_cv2, cursor_x, cursor_y)
            if frame is not None:
                if (HighFPS): jpg = Image.fromarray(cv2.resize(frame, (frame.shape[1]//2, frame.shape[0]//2)))
                else: jpg = Image.fromarray(frame)
                #jpg = Image.frombytes("RGB", frame.size, frame.bgra, "raw", "BGRX")
                tmpFile = BytesIO()
                jpg.save(tmpFile, 'JPEG')
                yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + tmpFile.getbuffer() + b'\r\n')  # Формат MJPEG

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_stream():
    global camera
    camera = bettercam.create(output_idx=int(number_entry.get()), output_color="RGB")
    time.sleep(0.1)
    camera.start(target_fps=144)
    time.sleep(0.1)

def stop_stream():
    global is_streaming
    is_streaming = False
    if camera:
        camera.stop()

def run_flask():
    start_stream()
    app.run(host='0.0.0.0', port=5000)

def update_qr_code(ip):
    qr = qrcode.make("http://" + ip + ":5000/video_feed")
    qr = qr.resize((300, 300))  # Изменяем размер QR-кода
    qr_photo = ImageTk.PhotoImage(qr)
    qr_label.config(image=qr_photo)
    qr_label.image = qr_photo  # Сохраняем ссылку на изображение
    root.geometry("300x600")

def start_streaming(ip):
    global is_streaming
    if not is_streaming:
        is_streaming = True
        threading.Thread(target=run_flask, daemon=True).start()
        update_qr_code(ip)
        preview_button.config(state="normal")
        start_button.config(text="Остановить трансляцию")  # Изменяем текст кнопки
    else:
        stop_streaming()

def stop_streaming():
    stop_stream()
    qr_label.config(image='')  # Убираем QR-код
    start_button.config(text="Начать трансляцию")  # Возвращаем текст кнопки
    preview_button.config(state="disabled")  # Отключаем кнопку "Предварительный просмотр"
    root.geometry("300x300")

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def open_browser():
    ip = ip_entry.get()  # Получаем IP-адрес из строки ввода
    if ip:
        webbrowser.open(f"http://{ip}:5000/video_feed")

def toggle_fps():
    global show_fps
    show_fps = not show_fps  # Переключаем состояние отображения FPS

def toggle_resorfps():
    global HighFPS
    HighFPS = not HighFPS  # Переключаем состояние отображения FPS

# Создание интерфейса Tkinter
root = tk.Tk()
root.title("RFConnect")

# Убираем кнопку разворачивания и увеличиваем ширину окна
root.resizable(False, False)
root.geometry("300x300")  # Устанавливаем ширину окна

# Поле для ввода IP-адреса
ip_label = tk.Label(root, text="Введите IP-адрес:")
ip_label.pack(pady=5)

ip_entry = tk.Entry(root)
ip_entry.pack(pady=5)

# Устанавливаем IP-адрес компьютера по умолчанию
default_ip = get_ip_address()
ip_entry.insert(0, default_ip)

start_button = tk.Button(root, text="Начать трансляцию", command=lambda: start_streaming(ip_entry.get()))
start_button.pack(pady=10)

preview_button = tk.Button(root, text="Предварительный просмотр", command=open_browser, state="disabled")
preview_button.pack(pady=10)

# Поле для ввода цифры
number_label = tk.Label(root, text="Введите номер монитора:")
number_label.pack(pady=5)

number_entry = tk.Entry(root)
number_entry.pack(pady=5)

number_entry.insert(0, "0")
# Чекбокс для отображения FPS
fps_var = tk.BooleanVar(value=False)  # По умолчанию чекбокс выключен
fps_checkbox = tk.Checkbutton(root, text="Отображать FPS", variable=fps_var, command=toggle_fps)
fps_checkbox.pack(pady=5)
# Чекбокс для выбора скорости
fps_var = tk.BooleanVar(value=False)  # По умолчанию чекбокс выключен
fps_checkbox = tk.Checkbutton(root, text="Высокое разрешение", variable=fps_var, command=toggle_resorfps)
fps_checkbox.pack(pady=5)
# Метки для предварительного просмотра и QR-кода
preview_label = tk.Label(root)
preview_label.pack(pady=10)

qr_label = tk.Label(root)
qr_label.pack(pady=10)

root.mainloop()