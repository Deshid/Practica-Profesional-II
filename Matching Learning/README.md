Matching Learning - Interfaz de captura y predicción

Resumen

Proyecto para capturar imágenes desde hasta 4 cámaras, guardar datasets "matching learning"
y ejecutar predicciones en tiempo real con modelos Keras (.h5).

Requisitos
- Python 3.8+
- OpenCV (cv2)
- TensorFlow (con Keras)
- Pillow (PIL)
- Opcional en Windows: pygrabber para obtener nombres de dispositivos

Uso rápido
1. Abrir la carpeta `Matching Learning`.
2. Ejecutar:

```bash
python Rec.py
```

3. En la pestaña "Camaras":
   - Pulsar "Detectar camaras" para listar índices.
   - Asignar fuentes a los 4 slots (o dejarlos sin asignar).
   - Seleccionar etiqueta y pulsar "Iniciar captura" para guardar imágenes en `dataset/<etiqueta>`.

4. En la pestaña "Prediccion IA":
   - Pulsar "Seleccionar modelo .h5" y cargar un modelo Keras.
   - Pulsar "Iniciar deteccion" para activar inferencia en tiempo real.

Estructura de carpetas
- `dataset/` : carpeta creada por el programa para guardar imagenes.
- `modelos/` : sugerido para colocar modelos .h5
- `Rec.py`   : interfaz principal (UI + lógica combinada)

Notas para desarrolladores
- El archivo `Rec.py` combina UI y lógica; para mantenimiento a largo plazo se recomienda
  separar en módulos: `ui.py`, `camaras.py`, `prediccion.py`, `utils.py`.
- Para pruebas sin UI, extraer las funciones de manejo de cámaras y predicción.

Contacto
- Si vas a compartir este repositorio, agrega instrucciones específicas de instalación
  (pip install -r requirements.txt) si lo deseas.
