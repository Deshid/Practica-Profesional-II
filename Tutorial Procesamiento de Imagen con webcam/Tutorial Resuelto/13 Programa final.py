import tkinter as tk
from tkinter import *
from tkinter import ttk
from PIL import Image
from PIL import ImageTk
import imutils
import cv2

# Crea ventana, define tamaño y título
ventana = tk.Tk()
ventana.geometry("1320x800")
ventana.resizable(0,0)
ventana.title("Proyecto procesamiento de imagen con webcam")

# Variables globales
global Captura, CapturaG, ImgRec
global x1_mouse, y1_mouse, x2_mouse, y2_mouse
x1_mouse = 0
y1_mouse = 0
x2_mouse = 0
y2_mouse = 0
seleccionando = False

# Inicia cámara web
def camara():
    global capture
    capture = cv2.VideoCapture(0)
    iniciar()

def iniciar():
    global capture
    if capture is not None:
        BCapturar.place(x=250,y=330,width=91,height=23)
        ret, frame = capture.read()
        if ret == True:
            frame = imutils.resize(frame, width=311)
            frame = imutils.resize(frame, height=241)
            ImagenCamara = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            im = Image.fromarray(ImagenCamara)
            img = ImageTk.PhotoImage(image=im)
            LImagen.configure(image= img)
            LImagen.image = img
            LImagen.after(5,iniciar)
        else:
            LImagen.image = ""
            capture.release()

def Capturar():
    global valor, Captura, CapturaG
    camara = capture
    return_value, image = camara.read()
    frame = imutils.resize(image, width=301)
    frame = imutils.resize(frame, height=221)
    CapturaG = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    Captura = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(Captura)
    img = ImageTk.PhotoImage(image=im)
    imG = Image.fromarray(CapturaG)
    imgG = ImageTk.PhotoImage(image=imG)
    GImagenROI.configure(image= imgG)
    GImagenROI.image = imgG
    LImagenRecorte.configure(image= img)
    LImagenRecorte.image = img
    
def rgb():
    global img_mask, img_aux,bin_imagen
    Minimos = (int(SRedI.get()), int(SGreenI.get()), int(SBlueI.get()))
    maximos = (int(SRedD.get()), int(SGreenD.get()), int(SBlueD.get()))
    img_mask = cv2.inRange(ImgRec, Minimos, maximos)
    img_aux = img_mask
    img_mask = Image.fromarray(img_mask)
    img_mask = ImageTk.PhotoImage(image=img_mask)
    LImagenManchas.configure(image=img_mask)
    LImagenManchas.image = img_mask
    _, bin_imagen= cv2.threshold(img_aux, 0, 255, cv2.THRESH_BINARY_INV)
    
def manchas():
    # Contar el número de pixeles con manchas
    num_pixels_con_manchas = cv2.countNonZero(bin_imagen)
    # Calcular el porcentaje de manchas
    porcentaje_manchas= 100 - (num_pixels_con_manchas / bin_imagen.size)*100
    # Contornos
    contornos = cv2.findContours(img_aux, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    # Cantidad de contorno
    num_formas = len(contornos)
    Cadena =f"Cantidad de manchas blancas: {num_formas}\nPorcentaje de manchas:\n porcentaje_área con manchas:{round(porcentaje_manchas, 2)}%"
    CajaTexto2.configure(state='normal')
    CajaTexto2.delete(1.0, tk.END)
    CajaTexto2.insert(1.0, Cadena)
    CajaTexto2.configure(state='disabled')


def umbralizacion():
    global thresh1, mask
    valor=int(numeroUmbra.get())
    ret,thresh1= cv2.threshold(CapturaG, valor, 255, cv2.THRESH_BINARY)
    Umbral = Image.fromarray(thresh1)
    Umbral = ImageTk.PhotoImage(image=Umbral)
    UImagen.configure(image=Umbral)
    UImagen.image = Umbral
    
    min = (valor, valor, valor)
    max = (255, 255, 255)
    mask = cv2.inRange(Captura, min, max)
    
def manchasG():
    # Contar el número de pixeles con manchas
    num_pixels_con_manchas = cv2.countNonZero(thresh1)
    # Calcular el porcentaje de manchas
    porcentaje_manchas= 100 - (num_pixels_con_manchas / thresh1.size)*100
    # Contornos
    contornos = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    
    # Cantidad de contornos
    manchas = len(contornos)
    Cadena = f"Cantidad de manchas blancas: {manchas}\n Porcentaje área sin manchas: {round(porcentaje_manchas, 2)}%"
    CajaTexto.configure(state="normal")
    CajaTexto.delete(1.0, tk.END)
    CajaTexto.insert(1.0, Cadena)
    CajaTexto.configure(state='disabled')
    
def mostrar_coordenadas(event):
    coordenadas['text']=f'x={event.x}, y={event.y}'

def inicio_recorte(event):
    global x1_mouse, y1_mouse, seleccionando
    x1_mouse = event.x
    y1_mouse = event.y
    seleccionando = True
    
def fin_recorte(event):
    global x1_mouse, y1_mouse, x2_mouse, y2_mouse, seleccionando
    x2_mouse = event.x
    y2_mouse = event.y
    seleccionando = False
    realizar_recorte_automatico()
    
def movimiento_mouse(event):
    global x1_mouse, y1_mouse, x2_mouse, y2_mouse, seleccionando, Captura
    if seleccionando and Captura is not None:
        x2_mouse = event.x
        y2_mouse = event.y
        dibujar_borde_recorte()

def dibujar_borde_recorte():
    global Captura
    if Captura is None:
        return
    
    img_preview = Captura.copy()
    
    # Obtener coordenadas del rectángulo
    px1 = min(x1_mouse, x2_mouse)
    py1 = min(y1_mouse, y2_mouse)
    px2 = max(x1_mouse, x2_mouse)
    py2 = max(y1_mouse, y2_mouse)
    
    # Asegurarse que están dentro de los límites
    px1 = max(0, px1)
    py1 = max(0, py1)
    px2 = min(img_preview.shape[1], px2)
    py2 = min(img_preview.shape[0], py2)
    
    # Dibujar rectángulo con borde de color (cyan)
    cv2.rectangle(img_preview, (px1, py1), (px2, py2), (0, 255, 255), 2)
    
    # Mostrar en el label
    im = Image.fromarray(img_preview)
    img = ImageTk.PhotoImage(image=im)
    LImagenRecorte.configure(image=img)
    LImagenRecorte.image = img

def realizar_recorte_automatico():
    global ImgRec, x1_mouse, y1_mouse, x2_mouse, y2_mouse, Captura
    
    if Captura is None:
        return
    
    # Obtener coordenadas del rectángulo
    px1 = min(x1_mouse, x2_mouse)
    py1 = min(y1_mouse, y2_mouse)
    px2 = max(x1_mouse, x2_mouse)
    py2 = max(y1_mouse, y2_mouse)
    
    # Asegurarse que están dentro de los límites
    px1 = max(0, px1)
    py1 = max(0, py1)
    px2 = min(Captura.shape[1], px2)
    py2 = min(Captura.shape[0], py2)
    
    # Evitar recortes de tamaño 0
    if px1 >= px2 or py1 >= py2:
        return
    
    # Realizar el recorte
    ImgRec = Captura[py1:py2, px1:px2]
    
    # Mostrar la imagen recortada
    Im = Image.fromarray(ImgRec)
    ImRec = ImageTk.PhotoImage(image=Im)
    LImagenROI.configure(image=ImRec)
    LImagenROI.image = ImRec
    
    # Mostrar las coordenadas usadas
    coordenadas['text'] = f'Recortado: x1={px1}, y1={py1}, x2={px2}, y2={py2}'
    
def recortar():
    global ImgRec
    # Esta función ahora no se usa, pero la dejamos por compatibilidad
    realizar_recorte_automatico()
    
# Botones
BCamara = tk.Button(ventana, text="Iniciar cámara", command=camara)
BCamara.place(x=60,y=330,width=90, height=23)
BCapturar = tk.Button(ventana, text="Tomar foto", command=Capturar)
BCapturar.place(x=250,y=330,width=91,height=23)
Bmanchas = tk.Button(ventana, text="Umbralización", command=rgb)
Bmanchas.place(x=760,y=640,width=100,height=23)
ManchasRGB = tk.Button(ventana, text="Análisis de manchas", command=manchas)
ManchasRGB.place(x=880,y=640,width=120,height=23)
BBinary = tk.Button(ventana, text="Umbralización", command=umbralizacion)
BBinary.place(x=800,y=310,width=90,height=23)
BManchasG = tk.Button(ventana, text="Análisis de Manchas", command=manchasG)    
BManchasG.place(x=1100,y=310,width=131,height=23)

# SpinBox
numeroUmbra = tk.Spinbox(ventana, from_=0, to=255)
numeroUmbra.place(x=900, y=331, width=42, height=23)
# SpinBox para coordenadas removidos - ahora se usan coordenadas del mouse
# x1 = tk.Spinbox(ventana, from_=0, to=298)
# x1.place(x=155, y=630, width=42, height=23)
# y1 = tk.Spinbox(ventana, from_=0, to=239)
# y1.place(x=240, y=630, width=42, height=23)
# x2 = tk.Spinbox(ventana, from_=1, to=298)
# x2.place(x=140, y=660, width=42, height=23)
# y2 = tk.Spinbox(ventana, from_=1, to=239)
# y2.place(x=240, y=660, width=42, height=23)

# Label
LRed = tk.Label(ventana, text="R")
LRed.place(x=530, y=640, width=21, height=16)
LGreen = tk.Label(ventana, text="G")
LGreen.place(x=530, y=680, width=21, height=16)
LBlue = tk.Label(ventana, text="B")
LBlue.place(x=530, y=720, width=21, height=16)
coordenadasTitulo = tk.Label(ventana, text="Coordenadas")
coordenadasTitulo.place(x=505, y=310)
coordenadas = tk.Label(ventana, text="")
coordenadas.place(x=495, y=330)
LRecorte = tk.Label(ventana, text="Arrastra para recortar")
LRecorte.place(x=80, y=615)

# Logo Universidad
logo = tk.PhotoImage(file="Tutorial Procesamiento de Imagen con webcam/13 Programa final - Procesamiento de imágenes usando webcam/LogoUBB.png")
logoUBB = ttk.Label(image=logo)
logoUBB.place(x=1250, y=615)

# Nombre alumna - carrera - profesor - Lab CIM
alumna = tk.Label(ventana, text="Estudiante practicante\n\n Paula Labra")
carrera = tk.Label(ventana, text="Ingeniería civil informática")
profesor= tk.Label(ventana, text="Profesor: XX").place(x=1250, y=700)
LabCIM = tk.Label(ventana, text="Lab CIM").place(x=1250, y=740)

# Cuadros de Imagen grises
LImagen = tk.Label(ventana,background="gray")
LImagen.place(x=50,y=50,width=300,height=240)
LImagenROI = tk.Label(ventana,background="gray")
LImagenROI.place(x=390,y=380,width=300,height=240)
GImagenROI = tk.Label(ventana,background="gray")
GImagenROI.place(x=390,y=50,width=300,height=240)
GImagenROI.bind('<Button-1>', mostrar_coordenadas)
UImagen = tk.Label(ventana,background="gray")
UImagen.place(x=730,y=50,width=301,height=240)
LImagenManchas = tk.Label(ventana,background="gray")
LImagenManchas.place(x=730,y=380,width=301,height=240)
LImagenRecorte = tk.Label(ventana,background="gray")
LImagenRecorte.place(x=50,y=380,width=301,height=240)
# Bindings para recorte automático con mouse
LImagenRecorte.bind('<Button-1>', inicio_recorte)
LImagenRecorte.bind('<B1-Motion>', movimiento_mouse)
LImagenRecorte.bind('<ButtonRelease-1>', fin_recorte)

# Cuadro de texto
CajaTexto = tk.Text(ventana, state="disabled")
CajaTexto.place(x=1055, y=50, width=225, height=220)
CajaTexto2 = tk.Text(ventana, state="disabled")
CajaTexto2.place(x=1055, y=380, width=225, height=220)

#RGB se inicia en 1, ya que si no, sale error de división por 0
SRedI = tk.Scale(ventana, from_=1, to=255, orient='horizontal')
SRedI.place(x=400, y=620)
SGreenI = tk.Scale(ventana, from_=1, to=255, orient='horizontal')
SGreenI.place(x=400, y=660)
SBlueI = tk.Scale(ventana, from_=1, to=255, orient='horizontal')
SBlueI.place(x=400, y=700)

SRedD = tk.Scale(ventana, from_=1, to=255, orient='horizontal')
SRedD.set(255)
SRedD.place(x=580, y=620)
SGreenD = tk.Scale(ventana, from_=1, to=255, orient='horizontal')
SGreenD.set(255)
SGreenD.place(x=580, y=660)
SBlueD = tk.Scale(ventana, from_=1, to=255, orient='horizontal')
SBlueD.set(255)
SBlueD.place(x=580, y=700)

#Pasos
paso1 = tk.Label(ventana, text="Paso 1: Iniciar cámara y tomar una foto")
paso1.place(x=70, y=20)
paso2 = tk.Label(ventana, text="Paso 2: Arrastra el mouse para seleccionar el área a recortar")
paso2.place(x=400, y=20)
paso3 = tk.Label(ventana, text="Paso 3a: Elegir un número entre 0 y 255 para umbralizar la imagen")
paso3.place(x=380, y=620)
paso4a = tk.Label(ventana, text="Paso 3b: Elegir un rango de números RGB para\n umbralizar la imagen a color")
paso4a.place(x=750, y=10)
paso4b = tk.Label(ventana, text="")
paso4b.place(x=750, y=700)
paso5 = tk.Label(ventana, text="Paso 4: Analizar las manchas en la imagen umbralizada")
paso5.place(x=1020, y=20)

ventana.mainloop()
