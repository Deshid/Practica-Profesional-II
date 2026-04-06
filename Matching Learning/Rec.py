import os
import re
import subprocess
import json
import importlib
import threading
import time
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
        self.raiz.resizable(True, True)
        self.raiz.bind("<F11>", self._alternar_pantalla_completa)
        self.raiz.bind("<Escape>", self._salir_pantalla_completa)
        try:
            self.raiz.state("zoomed")
        except tk.TclError:
            self.raiz.geometry(
                f"{self.raiz.winfo_screenwidth()}x{self.raiz.winfo_screenheight()}+0+0"
            )

        self.ancho_cuadro = 300
        self.alto_cuadro = 220

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
        self.variables_mensaje_slot = []
        self.imagen_negra_tk = None
        self.capturando = False
        self.ultimo_disparo = 0.0
        self.conteo_fotos = 0
        self.ultimo_id_disparo = 0
        self.intervalo_segundos = 3.0
        self.pausa_secuencial_segundos = 0.6
        self.ruta_objeto = None
        self.opciones_etiqueta_objeto = [
            "objeto_a",
            "objeto_b",
            "objeto_c",
            "objeto_d",
            "fondo_vacio",
        ]
        self.variable_mensaje_rojo = tk.StringVar(value="")

        self._construir_ui()
        self.raiz.bind("<Configure>", self._al_redimensionar)
        self.detectar_camaras()
        self._actualizar_vistas()

    def _construir_ui(self):
        self.raiz.columnconfigure(0, weight=1)
        self.raiz.rowconfigure(0, weight=1)

        contenedor = ttk.Frame(self.raiz, padding=8)
        contenedor.grid(row=0, column=0, sticky="nsew")
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(1, weight=1)

        ttk.Label(
            contenedor,
            text="Captura de datos para matching learning",
            font=("Segoe UI", 16, "bold"),
            anchor="center",
            justify="center",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        imagen_negra = Image.new("RGB", (self.ancho_cuadro, self.alto_cuadro), "black")
        self.imagen_negra_tk = ImageTk.PhotoImage(imagen_negra)

        cuadricula = ttk.Frame(contenedor)
        cuadricula.grid(row=1, column=0, sticky="nsew")
        for fila in range(2):
            cuadricula.rowconfigure(fila, weight=1)
        for columna in range(2):
            cuadricula.columnconfigure(columna, weight=1)

        for i in range(4):
            panel = ttk.LabelFrame(cuadricula, text=f"Camara {i + 1}")
            panel.grid(row=i // 2, column=i % 2, padx=4, pady=4, sticky="nsew")

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

            variable_mensaje = tk.StringVar(value="")
            etiqueta_mensaje = tk.Label(
                panel,
                textvariable=variable_mensaje,
                font=("Segoe UI", 10, "bold"),
                fg="#C00000",
                bg=self.raiz.cget("bg"),
                anchor="center",
                justify="center",
                pady=2,
            )
            etiqueta_mensaje.pack(fill="x", padx=4, pady=(0, 4))
            self.variables_mensaje_slot.append(variable_mensaje)

        self.fila_ruta = ttk.Frame(contenedor)
        self.fila_ruta.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        self.fila_ruta.columnconfigure(0, weight=1)

        self.etiqueta_mensaje_rojo = tk.Label(
            self.fila_ruta,
            textvariable=self.variable_mensaje_rojo,
            font=("Segoe UI", 11, "bold"),
            fg="#C00000",
            bg=self.raiz.cget("bg"),
            anchor="w",
            justify="left",
            wraplength=640,
            padx=4,
            pady=2,
        )
        self.etiqueta_mensaje_rojo.grid(row=0, column=0, sticky="ew")

        self.boton_copiar_ruta = ttk.Button(
            self.fila_ruta,
            text="Copiar ruta",
            command=self.copiar_ruta_sesion,
        )
        self.boton_copiar_ruta.grid(row=0, column=1, padx=(8, 0), sticky="e")
        self.boton_copiar_ruta.grid_remove()

        controles = ttk.Frame(contenedor, padding=(0, 6, 0, 0))
        controles.grid(row=3, column=0, sticky="ew")
        controles.columnconfigure(0, weight=1)

        fila_intervalo = ttk.Frame(controles)
        fila_intervalo.grid(row=0, column=0, sticky="w")

        ttk.Label(fila_intervalo, text="Etiqueta objeto:").grid(row=0, column=0)
        self.variable_objeto = tk.StringVar(value=self.opciones_etiqueta_objeto[0])
        self.combobox_etiqueta_objeto = ttk.Combobox(
            fila_intervalo,
            textvariable=self.variable_objeto,
            values=self.opciones_etiqueta_objeto,
            state="readonly",
            width=16,
        )
        self.combobox_etiqueta_objeto.grid(row=0, column=1, padx=(6, 10))

        ttk.Label(fila_intervalo, text="Intervalo entre fotos (s):").grid(row=0, column=2)
        self.variable_intervalo = tk.StringVar(value="3")
        ttk.Entry(fila_intervalo, textvariable=self.variable_intervalo, width=6).grid(
            row=0, column=3, padx=(6, 0)
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
        self.etiqueta_estado = tk.Label(
            controles,
            textvariable=self.variable_estado,
            font=("Segoe UI", 12, "bold"),
            bg="#111111",
            fg="#FFFFFF",
            anchor="w",
            justify="left",
            wraplength=640,
            padx=8,
            pady=6,
        )
        self.etiqueta_estado.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def _al_redimensionar(self, _evento=None):
        ancho_actual = max(400, self.raiz.winfo_width() - 40)
        self.etiqueta_estado.configure(wraplength=ancho_actual)
        self.etiqueta_mensaje_rojo.configure(wraplength=ancho_actual)

    def _alternar_pantalla_completa(self, _evento=None):
        estado_actual = self.raiz.state()
        if estado_actual == "zoomed":
            self.raiz.state("normal")
        else:
            self.raiz.state("zoomed")

    def _salir_pantalla_completa(self, _evento=None):
        self.raiz.state("normal")

    def _leer_intervalo(self):
        try:
            valor = float(self.variable_intervalo.get())
        except ValueError:
            valor = 3.0
        self.intervalo_segundos = max(0.5, valor)

    def iniciar_captura(self):
        self._leer_intervalo()
        etiqueta_objeto = self._normalizar_etiqueta_objeto(self.variable_objeto.get())
        if not etiqueta_objeto:
            self.variable_mensaje_rojo.set(
                "Define una etiqueta de objeto valida (ejemplo: objeto_a o fondo_vacio)."
            )
            self.boton_copiar_ruta.grid_remove()
            return

        self.capturando = True
        self.ultimo_disparo = 0.0
        self.conteo_fotos = 0
        self.ruta_objeto = self._asegurar_carpeta_objeto(etiqueta_objeto)
        self.ultimo_id_disparo = self._obtener_max_id_disparo(self.ruta_objeto)
        self.variable_mensaje_rojo.set("")
        self.boton_copiar_ruta.grid_remove()
        for variable_mensaje in self.variables_mensaje_slot:
            variable_mensaje.set("")

    def detener_captura(self):
        self.capturando = False
        if self.ruta_objeto:
            self.variable_mensaje_rojo.set(
                f"Captura detenida. Dataset guardado en: {self.ruta_objeto}"
            )
            self.boton_copiar_ruta.grid()
        else:
            self.variable_mensaje_rojo.set(
                "Captura detenida. No se guardaron imagenes en este dataset."
            )
            self.boton_copiar_ruta.grid_remove()

    def copiar_ruta_sesion(self):
        if self.ruta_objeto:
            self.raiz.clipboard_clear()
            self.raiz.clipboard_append(self.ruta_objeto)
            self.variable_mensaje_rojo.set(
                f"Ruta copiada al portapapeles: {self.ruta_objeto}"
            )
        else:
            self.variable_mensaje_rojo.set(
                "No hay ruta de dataset para copiar aun."
            )

    def _normalizar_etiqueta_objeto(self, etiqueta):
        etiqueta_limpia = (etiqueta or "").strip().lower()
        etiqueta_limpia = re.sub(r"\s+", "_", etiqueta_limpia)
        etiqueta_limpia = re.sub(r"[^a-z0-9_-]", "", etiqueta_limpia)
        return etiqueta_limpia

    def _asegurar_carpeta_objeto(self, etiqueta_objeto):
        base_script = os.path.dirname(os.path.abspath(__file__))
        carpeta_dataset = os.path.join(base_script, "dataset")
        os.makedirs(carpeta_dataset, exist_ok=True)

        # Carpeta para clase negativa recomendada en matching learning.
        os.makedirs(os.path.join(carpeta_dataset, "fondo_vacio"), exist_ok=True)

        ruta_objeto = os.path.join(carpeta_dataset, etiqueta_objeto)
        os.makedirs(ruta_objeto, exist_ok=True)
        return ruta_objeto

    def _obtener_max_id_disparo(self, ruta_objeto):
        maximo = 0
        patron = re.compile(r"^(\d+)_c\d+\.jpg$", re.IGNORECASE)

        try:
            nombres = os.listdir(ruta_objeto)
        except OSError:
            return 0

        for nombre in nombres:
            coincidencia = patron.match(nombre)
            if coincidencia:
                maximo = max(maximo, int(coincidencia.group(1)))

        return maximo

    def _guardar_capturas_intervalo(self, frames_por_slot):
        if not self.ruta_objeto:
            return 0, ["sin_frame", "sin_frame", "sin_frame", "sin_frame"]

        id_disparo = self.ultimo_id_disparo + 1
        guardadas = 0
        estado_por_slot = ["sin_frame", "sin_frame", "sin_frame", "sin_frame"]

        for slot, frame in enumerate(frames_por_slot):
            if frame is None:
                continue

            nombre = f"{id_disparo:03d}_c{slot + 1}.jpg"
            ruta_salida = os.path.join(self.ruta_objeto, nombre)
            if cv2.imwrite(ruta_salida, frame):
                guardadas += 1
                estado_por_slot[slot] = "capturado"
            else:
                estado_por_slot[slot] = "error_guardado"

        if guardadas > 0:
            self.ultimo_id_disparo = id_disparo

        return guardadas, estado_por_slot

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
        uso_por_indice = {}

        for slot, indice_asignado in enumerate(self.indices_asignados):
            if indice_asignado is None:
                continue
            uso_por_indice.setdefault(indice_asignado, []).append(slot + 1)

        for dispositivo in self.dispositivos:
            if dispositivo["indice"] not in self.indices_activos:
                continue

            opcion_base = self._armar_opcion(dispositivo)
            slots_en_uso = uso_por_indice.get(dispositivo["indice"], [])
            if slots_en_uso:
                slots_texto = ", ".join(str(s) for s in slots_en_uso)
                opcion = f"{opcion_base} [EN USO en camara {slots_texto}]"
            else:
                opcion = opcion_base

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
        self._actualizar_selectores()

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
                    self._actualizar_selectores()
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
                guardadas, _estado_por_slot = self._guardar_capturas_intervalo(frames_disponibles)
                if guardadas > 0:
                    self.conteo_fotos += 1

            for i in range(4):
                if self.indices_asignados[i] is None:
                    self.variables_mensaje_slot[i].set("")
                else:
                    self.variables_mensaje_slot[i].set(
                        f"capturando | fotos {self.conteo_fotos}"
                    )
        else:
            for i in range(4):
                self.variables_mensaje_slot[i].set("")

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