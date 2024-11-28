import telebot
from telebot import types 
import firebase_admin
from firebase_admin import db
import sys
from PyQt5 import QtWidgets
import os
from PyQt5 import QtCore, QtWidgets, QtGui, QtPrintSupport
import base64
from pathlib import Path
from shutil import rmtree
import time
import win32print
from PyQt5.QtPrintSupport import QPrinterInfo
from PIL import Image
import requests

event_data = []

def get_printer(printerName):
    printers = QPrinterInfo.availablePrinters()
    for printer in printers:
        if printerName in printer.printerName():
            return printer.printerName()
    return None

def remove_ip(printer):

    cleaned_name = printer.split('\\')[-1]  # Берем только последнюю часть после последнего '\\'
    return cleaned_name

def save_logFile(data):
    current_dir = os.getcwd()
    my_dir = os.path.join(current_dir)
    log_path = my_dir+"\\log"
    file_path = os.path.join(log_path, "history.txt")
    
    if 'User' not in data or not data['User']:
        data['User'] = 'Ink'
        
    images = data['Photos']
    num_images = len(images)  
    with open(file_path, "a") as file:
        file.write(f"Пользователь: {data['User']}, "
                f"Пользователь: {data['Name']}, "
                f"напечатал в: {data['Date']}, "
                f"ориентация: {data['orientation']}, "
                f"тип печати: {data['sides']}, "
                f"количество копий: {data['copies']},"
                f"Количество изображений: {num_images}\n")
        file.close() 

def _print_images(printer, image_path):
    image_files = os.listdir(image_path)
    painter = QtGui.QPainter()       
    painter.begin(printer)
    
    for i, image_file in enumerate(image_files):
        full_image_path = os.path.join(image_path, image_file) 
        pixmap = QtGui.QPixmap(full_image_path)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        image_width, image_height = pixmap.width(), pixmap.height()
        page_width, page_height = printer.pageRect().width(), printer.pageRect().height()

        #if image_width > page_width or image_height > page_height:
        #pixmap = pixmap.scaled(page_width, page_height, QtCore.Qt.KeepAspectRatio)
        pixmap = pixmap.scaled(page_width, page_height, QtCore.Qt.KeepAspectRatio)

        painter.drawPixmap(0, 0, pixmap)
        if i < len(image_files) - 1:
            printer.newPage() 
            
        
    painter.end()
    
    
def print_on_print(printer,image_path):
        pd = QtPrintSupport.QPrintDialog(printer)
        pd.setOptions(QtPrintSupport.QAbstractPrintDialog.PrintToFile |
                     QtPrintSupport.QAbstractPrintDialog.PrintSelection)

        _print_images(printer,image_path)    
        
def get_image_orientation(image_path):
    """Determine if the image is 'Книжная' or 'Альбомная'."""
    with Image.open(image_path) as img:
        width, height = img.size
        return '1' if width > height else '0'        
    
def print_file(data):
    save_logFile(data)
    
    app = QtWidgets.QApplication(sys.argv) 
    #printer = QtPrintSupport.QPrinter()    
    #printer.setResolution(600) 
    #cleaned_printers = remove_ip(data['printer'])
    #printer.setPrinterName(data['printer'])
    
    
    
    printer_name = get_printer(data['printer'])
    if printer_name is None:
        printer.setPrinterName(win32print.GetDefaultPrinter())
        return
    printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
    printer.setResolution(600)
    printer.setPrinterName(printer_name)
    
    
    printer.setCopyCount(int(data['copies']))
    

        
    if data['sides']=='Одностороняя':
        printer.setDuplex(int(0)) 
    elif data['sides']=='Двусторонняя':
        printer.setDuplex(int(1))  # 1 Двустороняя

    #Настраиваем рабочую папку
    current_dir = os.getcwd()
    my_dir = os.path.join(current_dir)
    image_path = my_dir+"\\output"

    #Очищаем папку перед печатью чтобы не напечатать лишнего
    for path in Path(image_path).glob('*'):
        if path.is_dir():
            rmtree(path)
        else:
            path.unlink()
    
    #Преобразуем base64 в нормальные фото
    i=0 
    images = data['Photos']
    for element in images:
        i+=1
        with open(f'{image_path}\\{i}.png', "wb") as fh:
            fh.write(base64.decodebytes(element.encode()))
            fh.close()
            
    if data['orientation'] == 'альбомная':
        printer.setPageOrientation(int(1))
    elif data['orientation'] == 'книжная':
        printer.setPageOrientation(int(0))
    elif data['orientation'] == 'авто': 

        image_file_path = f'{image_path}\\1.png'
        orientation = get_image_orientation(image_file_path)
        printer.setPageOrientation(int(orientation))
            
    print_on_print(printer,image_path)


def listener(event): 
    if event.data==None:
        print('delete')
    else:
        if event.path == '/':
            print('connect')
        else:
            print_file(event.data)

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
#cred_obj = firebase_admin.credentials.Certificate('c:\\Users\\admin\\Documents\\tg-print-app-firebase-adminsdk-p1y91-4eb5e13285.json')
cred_obj = firebase_admin.credentials.Certificate('c:\\Users\\admin\\Documents\\print-chptk-firebase-adminsdk-1qjq9-c65970a3ae.json')
#default_app = firebase_admin.initialize_app(cred_obj, {
#	'databaseURL':"https://tg-print-app-default-rtdb.firebaseio.com"
#	})
default_app = firebase_admin.initialize_app(cred_obj, {
	'databaseURL':"https://print-chptk-default-rtdb.firebaseio.com"
	})
ref = db.reference('/Print')
ref._listen_with_session(listener)


ref_printers = db.reference('/Printers')
