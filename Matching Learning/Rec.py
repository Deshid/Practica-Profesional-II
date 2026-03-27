import os
import re
import subprocess
import json
import importlib
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk

os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")
import cv2
from PIL import Image, ImageTk

class InterfazCuatroCamaras:
    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("UI - 4 Camaras")
        self.raiz.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.ancho_cuadro = 311
        self.alto_cuadro = 241

        self.capturas = [None, None, None, None]
        self.dispositivos = []
        self.variables_selector = []
        self.comboboxes = []
        self.opcion_a_indice = {}
        self.indices_activos = set()
        self.indices_asignados = [None, None, None, None]
        self.version_slot = [0, 0, 0, 0]
        self.cargando_slot = [False, False, False, False]
        self.etiquetas_video = []
        self.imagen_negra_tk = None
        self.capturando = False
        self.ultimo_disparo = 0.0
        self.conteo_fotos = 0
        self.intervalo_segundos = 3.0
        self.pausa_secuencial_segundos = 0.6
        self.ruta_sesion = None

        self._construir_ui()
        self._bloquear_tamano_inicial()
        self.detectar_camaras()
        self._actualizar_vistas()

    def _construir_ui(self):
        self.raiz.columnconfigure(0, weight=1)
        self.raiz.rowconfigure(0, weight=1)

        contenedor = ttk.Frame(self.raiz, padding=10)
        contenedor.grid(row=0, column=0, sticky="nsew")
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)

        imagen_negra = Image.new("RGB", (self.ancho_cuadro, self.alto_cuadro), "black")
        self.imagen_negra_tk = ImageTk.PhotoImage(imagen_negra)

        cuadricula = ttk.Frame(contenedor)
        cuadricula.grid(row=0, column=0, sticky="nsew")
        for fila in range(2):
            cuadricula.rowconfigure(fila, weight=1)
        for columna in range(2):
            cuadricula.columnconfigure(columna, weight=1)

        for i in range(4):
            panel = ttk.LabelFrame(cuadricula, text=f"Camara {i + 1}")
            panel.grid(row=i // 2, column=i % 2, padx=6, pady=6, sticky="nsew")

            fila_selector = ttk.Frame(panel)
            fila_selector.pack(fill="x", padx=4, pady=(4, 0))
            ttk.Label(fila_selector, text="Fuente:").pack(side="left")

            variable_selector = tk.StringVar(value="No asignada")
            combobox = ttk.Combobox(
                fila_selector,
                textvariable=variable_selector,
                values=["No asignada"],
                state="readonly",
                width=30,
            )
            combobox.pack(side="left", padx=(6, 0))
            combobox.bind("<<ComboboxSelected>>", lambda _e, slot=i: self._al_cambiar_selector(slot))
            self.variables_selector.append(variable_selector)
            self.comboboxes.append(combobox)

            vista = tk.Label(
                panel,
                text=f"Camara {i + 1}\nSin senal",
                image=self.imagen_negra_tk,
                compound="center",
                bg="black",
                fg="white",
                font=("Segoe UI", 12, "bold"),
            )
            vista.pack(padx=4, pady=4)
            self.etiquetas_video.append(vista)

        controles = ttk.Frame(contenedor, padding=(0, 8, 0, 0))
        controles.grid(row=1, column=0, sticky="ew")
        controles.columnconfigure(0, weight=1)

        fila_intervalo = ttk.Frame(controles)
        fila_intervalo.grid(row=0, column=0, sticky="w")

        ttk.Label(fila_intervalo, text="Intervalo entre fotos (s):").grid(row=0, column=0)
        self.variable_intervalo = tk.StringVar(value="3")
        ttk.Entry(fila_intervalo, textvariable=self.variable_intervalo, width=6).grid(
            row=0, column=1, padx=(6, 0)
        )

        botones = ttk.Frame(controles)
        botones.grid(row=0, column=1, sticky="e")
        ttk.Button(botones, text="Iniciar", command=self.iniciar_captura).grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Button(botones, text="Detener", command=self.detener_captura).grid(row=0, column=1)
        ttk.Button(
            botones,
            text="Detectar camaras",
            command=self.detectar_camaras,
        ).grid(row=0, column=2, padx=(6, 0))

        self.variable_estado = tk.StringVar(value="Detectando camaras...")
        ttk.Label(controles, textvariable=self.variable_estado, font=("Segoe UI", 11, "bold")).grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )

    def _bloquear_tamano_inicial(self):
        self.raiz.update_idletasks()
        ancho = self.raiz.winfo_width()
        alto = self.raiz.winfo_height()
        self.raiz.minsize(ancho, alto)
        self.raiz.maxsize(ancho, alto)
        self.raiz.resizable(False, False)

    def _leer_intervalo(self):
        try:
            valor = float(self.variable_intervalo.get())
        except ValueError:
            valor = 3.0
        self.intervalo_segundos = max(0.5, valor)

    def iniciar_captura(self):
        self._leer_intervalo()
        self.capturando = True
        self.ultimo_disparo = 0.0
        self.conteo_fotos = 0
        self.ruta_sesion = None

    def detener_captura(self):
        self.capturando = False

    def _asegurar_sesion_captura(self):
        if self.ruta_sesion is None:
            marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.ruta_sesion = os.path.join("capturas_intervalo", f"sesion_{marca_tiempo}")
            os.makedirs(self.ruta_sesion, exist_ok=True)

        return self.ruta_sesion

    def _guardar_capturas_intervalo(self, frames_por_slot):
        carpeta_sesion = self._asegurar_sesion_captura()
        guardadas = 0

        for slot, frame in enumerate(frames_por_slot):
            if frame is None:
                continue

            carpeta_camara = os.path.join(carpeta_sesion, f"camara_{slot + 1}")
            os.makedirs(carpeta_camara, exist_ok=True)

            nombre = f"foto_{self.conteo_fotos + 1:05d}_cam{slot + 1}.jpg"
            ruta_salida = os.path.join(carpeta_camara, nombre)
            if cv2.imwrite(ruta_salida, frame):
                guardadas += 1

        return guardadas

    def _abrir_camara(self, indice):
        # Para indices de Windows, DSHOW suele responder mas rapido y evita pruebas extra.
        camara = cv2.VideoCapture(indice, cv2.CAP_DSHOW)
        if not camara.isOpened():
            camara.release()
            return None

        camara.set(cv2.CAP_PROP_FRAME_WIDTH, self.ancho_cuadro)
        camara.set(cv2.CAP_PROP_FRAME_HEIGHT, self.alto_cuadro)
        return camara

    def _leer_frame_seguro(self, camara):
        try:
            return camara.read()
        except cv2.error:
            return False, None

    def _obtener_nombres_sistema(self):
        try:
            modulo = importlib.import_module("pygrabber.dshow_graph")
            FilterGraph = getattr(modulo, "FilterGraph")
            return FilterGraph().get_input_devices()
        except Exception:
            return []

    def _normalizar_nombre(self, nombre):
        return " ".join(nombre.lower().split())

    def _formatear_puerto(self, location):
        if not location:
            return "desconocido"

        texto = str(location).strip()
        patron = re.search(r"Port_#(\d+)\.Hub_#(\d+)", texto, flags=re.IGNORECASE)
        if patron:
            puerto, hub = patron.groups()
            return f"Hub {int(hub)} / Puerto {int(puerto)}"

        return texto

    def _obtener_info_usb_windows(self):
        if os.name != "nt":
            return {}

        comando = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_PnPEntity "
            "| Where-Object { $_.Service -eq 'usbvideo' -and $_.Name } "
            "| Select-Object Name, PNPDeviceID, LocationInformation "
            "| ConvertTo-Json -Compress",
        ]

        try:
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except Exception:
            return {}

        salida = (resultado.stdout or "").strip()
        if not salida:
            return {}

        try:
            data = json.loads(salida)
        except Exception:
            return {}

        if isinstance(data, dict):
            data = [data]

        mapa = {}
        for item in data:
            nombre = item.get("Name")
            if not nombre:
                continue

            clave = self._normalizar_nombre(nombre)
            info = {
                "nombre": nombre,
                "pnp_id": item.get("PNPDeviceID", ""),
                "puerto": self._formatear_puerto(item.get("LocationInformation", "")),
            }
            mapa.setdefault(clave, []).append(info)

        for clave in mapa:
            mapa[clave].sort(key=lambda x: x["puerto"])

        return mapa

    def _detectar_dispositivos(self):
        nombres = self._obtener_nombres_sistema()
        mapa_usb = self._obtener_info_usb_windows()
        dispositivos = []

        if nombres:
            # pygrabber devuelve los nombres reales del sistema en orden de indice DirectShow.
            usados_por_nombre = {}
            for i, nombre in enumerate(nombres):
                clave = self._normalizar_nombre(nombre)
                usados = usados_por_nombre.get(clave, 0)
                info_usb = mapa_usb.get(clave, [])
                puerto_usb = (
                    info_usb[usados]["puerto"]
                    if usados < len(info_usb)
                    else f"indice {i}"
                )
                usados_por_nombre[clave] = usados + 1

                dispositivos.append(
                    {
                        "indice": i,
                        "nombre": nombre,
                        "puerto": puerto_usb,
                    }
                )

        # En algunos hubs USB, Windows reporta pocos nombres aunque haya mas webcams conectadas.
        # Agregamos indices candidatos para seleccion manual por cuadro (sin abrirlos aqui).
        if len(dispositivos) < 4:
            indices_existentes = {d["indice"] for d in dispositivos}
            for i in range(8):
                if i not in indices_existentes:
                    dispositivos.append(
                        {
                            "indice": i,
                            "nombre": f"Camara candidato idx {i}",
                            "puerto": f"indice {i}",
                        }
                    )

        if not dispositivos:
            return [
                {
                    "indice": i,
                    "nombre": f"Camara candidato idx {i}",
                    "puerto": f"indice {i}",
                }
                for i in range(8)
            ]

        return dispositivos

    def _probar_indice(self, indice):
        camara = self._abrir_camara(indice)
        if camara is None or not camara.isOpened():
            return False

        try:
            ok, _frame = self._leer_frame_seguro(camara)
            return bool(ok)
        finally:
            camara.release()

    def _armar_opcion(self, dispositivo):
        return (
            f"{dispositivo['nombre']} | {dispositivo.get('puerto', 'desconocido')} "
            f"[idx {dispositivo['indice']}]"
        )

    def _actualizar_selectores(self):
        self.opcion_a_indice = {}
        opciones = ["No asignada"]

        for dispositivo in self.dispositivos:
            if dispositivo["indice"] not in self.indices_activos:
                continue
            opcion = self._armar_opcion(dispositivo)
            opciones.append(opcion)
            self.opcion_a_indice[opcion] = dispositivo["indice"]

        for slot in range(4):
            self.comboboxes[slot]["values"] = opciones
            indice = self.indices_asignados[slot]
            if indice is None:
                self.variables_selector[slot].set("No asignada")
            else:
                texto = next(
                    (o for o, i in self.opcion_a_indice.items() if i == indice),
                    "No asignada",
                )
                self.variables_selector[slot].set(texto)

    def _asignar_camara_slot(self, slot, indice):
        self.version_slot[slot] += 1
        version_actual = self.version_slot[slot]

        if self.capturas[slot] is not None and self.capturas[slot].isOpened():
            self.capturas[slot].release()

        self.capturas[slot] = None
        self.indices_asignados[slot] = None
        self.cargando_slot[slot] = False

        if indice is None:
            return

        self.cargando_slot[slot] = True

        def tarea_apertura(slot_local, indice_local, version_local):
            camara = self._abrir_camara(indice_local)

            def finalizar():
                if version_local != self.version_slot[slot_local]:
                    if camara is not None and camara.isOpened():
                        camara.release()
                    return

                self.cargando_slot[slot_local] = False
                if camara is not None and camara.isOpened():
                    self.capturas[slot_local] = camara
                    self.indices_asignados[slot_local] = indice_local
                else:
                    self.variable_estado.set(f"No se pudo abrir la camara del indice {indice_local}")

            self.raiz.after(0, finalizar)

        threading.Thread(
            target=tarea_apertura,
            args=(slot, indice, version_actual),
            daemon=True,
        ).start()

    def _encender_slots_secuencial(self, indices_detectados):
        limite = min(4, len(indices_detectados))

        for slot in range(4):
            self._asignar_camara_slot(slot, None)

        if limite == 0:
            self.variable_estado.set("No se pudo abrir ninguna camara durante la deteccion secuencial")
            return

        def abrir_slot(slot):
            if slot >= limite:
                self.variable_estado.set(
                    f"Deteccion secuencial finalizada: {limite} camaras encendidas"
                )
                return

            indice = indices_detectados[slot]
            self.variable_estado.set(
                f"Encendiendo secuencialmente camara {slot + 1} (idx {indice})..."
            )
            self._asignar_camara_slot(slot, indice)
            self.raiz.after(
                int(self.pausa_secuencial_segundos * 1000),
                lambda: abrir_slot(slot + 1),
            )

        abrir_slot(0)

    def _al_cambiar_selector(self, slot):
        opcion = self.variables_selector[slot].get()
        if opcion == "No asignada":
            self._asignar_camara_slot(slot, None)
            return

        indice = self.opcion_a_indice.get(opcion)
        self._asignar_camara_slot(slot, indice)

    def detectar_camaras(self):
        for slot in range(4):
            self._asignar_camara_slot(slot, None)

        self.indices_activos.clear()
        self.dispositivos = self._detectar_dispositivos()
        self._actualizar_selectores()

        nombres = [d["nombre"] for d in self.dispositivos]
        if self.dispositivos:
            nombres_reales = len([n for n in nombres if not n.startswith("Camara candidato idx")])
            self.variable_estado.set(
                f"Detectadas {nombres_reales} camaras por sistema. Iniciando prueba secuencial..."
            )
        else:
            self.variable_estado.set("No se detectaron camaras disponibles")
            return

        def tarea_deteccion_secuencial():
            indices_candidatos = []
            vistos = set()
            for dispositivo in self.dispositivos:
                indice = dispositivo["indice"]
                if indice in vistos:
                    continue
                vistos.add(indice)
                indices_candidatos.append(indice)

            indices_detectados = []
            for posicion, indice in enumerate(indices_candidatos, start=1):
                self.raiz.after(
                    0,
                    lambda p=posicion, total=len(indices_candidatos), i=indice: self.variable_estado.set(
                        f"Probando secuencialmente indice {i} ({p}/{total})..."
                    ),
                )

                if self._probar_indice(indice):
                    indices_detectados.append(indice)
                    if len(indices_detectados) >= 4:
                        break

                time.sleep(self.pausa_secuencial_segundos)

            def finalizar_deteccion():
                self.indices_activos = set(indices_detectados)
                self._actualizar_selectores()
                self._encender_slots_secuencial(indices_detectados)

            self.raiz.after(0, finalizar_deteccion)

        threading.Thread(target=tarea_deteccion_secuencial, daemon=True).start()

    def _inicializar_camaras(self):
        self.detectar_camaras()

    def _actualizar_vistas(self):
        conectadas = 0
        frames_disponibles = [None, None, None, None]

        for i, camara in enumerate(self.capturas):
            ok, frame = (
                self._leer_frame_seguro(camara)
                if camara is not None and camara.isOpened()
                else (False, None)
            )

            if ok and frame is not None:
                conectadas += 1
                frame = cv2.resize(frame, (self.ancho_cuadro, self.alto_cuadro))
                frames_disponibles[i] = frame.copy()
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                imagen = Image.fromarray(frame_rgb)
                imagen_tk = ImageTk.PhotoImage(imagen)
                self.etiquetas_video[i].configure(image=imagen_tk, text="", bg="black")
                self.etiquetas_video[i].imagen_tk = imagen_tk
            else:
                texto_sin_senal = (
                    f"Camara {i + 1}\nAbriendo..."
                    if self.cargando_slot[i]
                    else f"Camara {i + 1}\nSin senal / no asignada"
                )
                self.etiquetas_video[i].configure(
                    image=self.imagen_negra_tk,
                    text=texto_sin_senal,
                    bg="black",
                    fg="white",
                    compound="center",
                )
                self.etiquetas_video[i].imagen_tk = self.imagen_negra_tk

        if self.capturando:
            ahora = time.time()
            if ahora - self.ultimo_disparo >= self.intervalo_segundos:
                self.ultimo_disparo = ahora
                guardadas = self._guardar_capturas_intervalo(frames_disponibles)
                if guardadas > 0:
                    self.conteo_fotos += 1

        estado_captura = "activa" if self.capturando else "detenida"
        asignadas = [i for i in self.indices_asignados if i is not None]
        self.variable_estado.set(
            "Camaras activas: "
            f"{conectadas}/4 | indices asignados: {asignadas} | captura: {estado_captura} | fotos: {self.conteo_fotos}"
        )
        self.raiz.after(33, self._actualizar_vistas)

    def cerrar(self):
        for camara in self.capturas:
            if camara is not None and camara.isOpened():
                camara.release()
        self.raiz.destroy()


if __name__ == "__main__":
    raiz = tk.Tk()
    app = InterfazCuatroCamaras(raiz)
    raiz.mainloop()