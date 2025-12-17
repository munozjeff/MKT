import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from PIL import Image, ImageTk
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import numpy as np
from selenium.webdriver.chrome.service import Service
import shutil
from selenium.common.exceptions import NoSuchElementException
import threading
import re
from datetime import datetime
from faker import Faker
import random

fake = Faker()

# Plantillas por tema
saludos = [
    "¡Hola {name}! ¿Cómo te encuentras hoy?",
    "¡Hey {name}! Nos alegra mucho verte por aquí.",
    "¡Qué tal, {name}! ¿Cómo van las cosas?",
    "¡Hola de nuevo, {name}! Siempre es un gusto saludarte.",
    "¡Bienvenido, {name}! ¿Listo para un día productivo?",
    "¡Hola! Nos alegra mucho que estés con nosotros, {name}.",
    "¡Hola {name}! Esperamos que estés teniendo un excelente día.",
    "¡Qué alegría verte de nuevo, {name}!",
    "¡Hey! Aquí estamos para lo que necesites, {name}.",
    "¡Hola {name}! Un placer saludarte otra vez."
]


mensajes_bienvenida = [
    "Esperamos que todo esté yendo según lo planeado.",
    "Si tienes algo en mente, no dudes en compartirlo.",
    "Estamos aquí para ayudarte a alcanzar tus metas.",
    "¿Qué tal si comenzamos revisando tus pendientes?",
    "Esperamos que encuentres lo que necesitas.",
    "Aquí estamos para resolver cualquier duda.",
    "¡Estamos para apoyarte en lo que necesites!",
    "¡Es un buen momento para avanzar con tus planes!",
    "Si tienes alguna idea, estaremos encantados de escucharla.",
    "Esperamos que encuentres valor en cada paso del proceso."
]


recordatorios = [
    "Recuerda completar tu actividad relacionada con {tema}.",
    "Tienes un evento programado para el {fecha}, ¡no lo olvides!",
    "¿Ya revisaste tus tareas pendientes de {seccion}?",
    "El {fecha} es clave para el avance en {tema}.",
    "Es un buen momento para enfocarte en {tema}.",
    "Tómate unos minutos para trabajar en tu proyecto de {tema}.",
    "Mantén al día tus notas en {seccion}.",
    "El progreso en {tema} es fundamental para alcanzar tus objetivos.",
    "Revisar {seccion} te ayudará a mantener el control.",
    "No olvides que puedes consultar {seccion} para más información."
]


detalles_recordatorio = [
    "Esto marcará una gran diferencia en tus resultados.",
    "Aprovecha al máximo las herramientas disponibles.",
    "Recuerda que pequeños pasos te llevan a grandes logros.",
    "Hacer esto ahora te evitará problemas más adelante.",
    "Es importante que dediques tiempo a esto.",
    "¡Tú puedes hacerlo! No dudes en seguir adelante.",
    "Nos aseguraremos de que tengas todo lo necesario para avanzar.",
    "Esto te acercará más a tus metas.",
    "Tu dedicación ahora hará que el futuro sea más sencillo.",
    "Estamos aquí para ayudarte a mantenerte en el camino correcto."
]

despedidas = [
    "¡Hasta luego, {name}! Cuida de ti.",
    "Seguimos en contacto. ¡Éxitos en tus proyectos!",
    "¡Nos vemos pronto, {name}! Cualquier cosa, aquí estamos.",
    "¡Gracias por estar con nosotros, {name}! Que tengas un gran día.",
    "Espero verte pronto de nuevo, {name}. ¡Hasta la próxima!",
    "Recuerda que estamos aquí para apoyarte. ¡Hasta luego!",
    "Cuídate, {name}. ¡Nos vemos pronto!",
    "¡Adelante, {name}! Todo lo mejor para ti.",
    "¡Hasta la próxima, {name}! Sigue avanzando.",
    "Estamos para lo que necesites, {name}. ¡Hasta luego!"
]

preguntas = [
    "¿Cómo te has sentido respecto a tus avances en {tema}?",
    "¿Ya exploraste todas las opciones en {seccion}?",
    "¿Tienes alguna duda o inquietud sobre {tema}?",
    "¿Has notado algún cambio en tu progreso con {tema}?",
    "¿Qué tal si revisamos juntos tus pendientes?",
    "¿Ya organizaste tus actividades para esta semana?",
    "¿Hay algo que podamos hacer para facilitar tu trabajo?",
    "¿Cómo te está ayudando {seccion} en tus tareas actuales?",
    "¿Ya le echaste un vistazo a las novedades de {tema}?",
    "¿Qué opinas sobre tus avances en {seccion}?"
]

sugerencias = [
    "Te recomendamos dedicar 15 minutos a {tema} hoy.",
    "Podrías revisar las herramientas disponibles en {seccion}.",
    "Organiza tus tareas de esta semana para evitar contratiempos.",
    "Prueba enfocarte en una actividad a la vez, comenzando por {tema}.",
    "Dedica un tiempo a planificar tus metas del mes.",
    "Explora nuevas ideas o estrategias en {seccion}.",
    "Establece prioridades claras para tus proyectos de {tema}.",
    "Tómate un momento para reflexionar sobre tus progresos.",
    "Busca inspiración revisando tus logros pasados en {seccion}.",
    "Apóyate en el equipo para superar cualquier desafío."
]



informe = []


class App(tk.Tk):
    def __init__(self,driver_path='chromedriver.exe'):
        super().__init__()
        self.title("Aplicación de Envío de Mensajes")
        self.geometry("1000x600")

        # Obtener la ruta del directorio donde se encuentra el script
        self.script_dir = os.path.abspath(os.path.dirname(__file__))

        # Crear el contenedor principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Crear la barra de navegación lateral
        self.sidebar = ttk.Frame(main_frame, width=200, relief=tk.RAISED)
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)

        # Crear el área principal
        self.main_area = ttk.Frame(main_frame)
        self.main_area.pack(fill=tk.BOTH, expand=True)

        # Añadir botones al menú lateral
        self.create_sidebar_buttons()
        # Variable donde se almacenara la carpet de facturas seleccionada
        self.selected_folder = None

        self.cancel_flag = False
        # Variable para almacenar la imagen cargada
        self.image = None
        # Variable para almacenar la instancia del navegador
        #self.browser = None
        # Variable para almacenar el path del archivo de Excel
        self.file_path = None

        self.driver_path = os.path.join(self.script_dir, driver_path)
        self.service = Service(self.driver_path)
        self.driver = None
        self.wait = None

    def create_sidebar_buttons(self):
        # Botón para Agregar Contactos
        btn_add_contacts = ttk.Button(self.sidebar, text="Agregar Contactos", command=self.add_contacts)
        btn_add_contacts.pack(fill=tk.X, pady=5)

        # Botón para Campañas Predeterminadas
        btn_pred_campaigns = ttk.Button(self.sidebar, text="Campañas Predeterminadas", command=self.pred_campaigns)
        btn_pred_campaigns.pack(fill=tk.X, pady=5)

        # Botón para Campañas Dinámicas
        btn_dynamic_campaigns = ttk.Button(self.sidebar, text="Campañas Dinámicas", command=self.dynamic_campaigns)
        btn_dynamic_campaigns.pack(fill=tk.X, pady=5)

        # Botón para Enviar Mensajes
        btn_send_messages = ttk.Button(self.sidebar, text="Enviar Mensajes", command=self.send_messages)
        btn_send_messages.pack(fill=tk.X, pady=5)

         # Botón para Anti Spam (Nuevo botón)
        # btn_anti_spam = ttk.Button(self.sidebar, text="Anti Spam", command=self.anti_spam)
        # btn_anti_spam.pack(fill=tk.X, pady=5)

    def load_contacts(self):
        self.clear_main_area()
        lbl = ttk.Label(self.main_area, text="Funcionalidad para Cargar Contactos")
        lbl.pack(pady=20)

    def add_contacts(self):
        """Cargar y gestionar la lista de contactos"""
        self.clear_main_area()
        
        # Crear el frame para los contactos
        contacts_frame = ttk.Frame(self.main_area)
        contacts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Verificar si el archivo `contactos.json` existe y cargar contactos
        self.contacts_file = os.path.join(self.script_dir, "data", "contactos.json")
        self.contacts_list = []
        
        if os.path.exists(self.contacts_file):
            with open(self.contacts_file, "r", encoding="utf-8") as f:
                self.contacts_list = json.load(f)
        
        # Crear la tabla de contactos
        columns = ("Número de Teléfono", "Nombre")
        self.contacts_tree = ttk.Treeview(contacts_frame, columns=columns, show="headings")
        self.contacts_tree.heading("Número de Teléfono", text="Número de Teléfono")
        self.contacts_tree.heading("Nombre", text="Nombre")
        self.contacts_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Llenar la tabla con los contactos
        for contact in self.contacts_list:
            self.contacts_tree.insert("", "end", values=(contact["telefono"], contact["nombre"]))

        # Asociar evento de doble clic en la tabla de contactos
        self.contacts_tree.bind("<Double-1>", self.on_contact_double_click)

        # Frame para opciones de agregar y eliminar contactos
        manage_frame = ttk.Frame(contacts_frame)
        manage_frame.pack(pady=10)

        # Campo para ingresar número de teléfono
        ttk.Label(manage_frame, text="Número de Teléfono:").grid(row=0, column=0, padx=5)
        self.entry_phone = ttk.Entry(manage_frame)
        self.entry_phone.grid(row=0, column=1, padx=5)

        # Campo para ingresar nombre
        ttk.Label(manage_frame, text="Nombre:").grid(row=1, column=0, padx=5)
        self.entry_name = ttk.Entry(manage_frame)
        self.entry_name.grid(row=1, column=1, padx=5)

        # Botón para agregar contacto
        btn_add = ttk.Button(manage_frame, text="Agregar Contacto", command=self.add_contact)
        btn_add.grid(row=2, column=0, columnspan=2, pady=5)

        # Botón para eliminar contacto seleccionado
        btn_delete = ttk.Button(manage_frame, text="Eliminar Contacto", command=self.delete_contact)
        btn_delete.grid(row=3, column=0, columnspan=2, pady=5)

    def on_contact_double_click(self, event):
        """Cargar datos del contacto en los campos de entrada para editar"""
        # Obtener el contacto seleccionado
        selected_item = self.contacts_tree.selection()
        if not selected_item:
            return  # Si no hay contacto seleccionado, salir

        # Obtener los datos del contacto seleccionado
        phone = self.contacts_tree.item(selected_item)["values"][0]
        name = self.contacts_tree.item(selected_item)["values"][1]

        # Cargar los datos en los campos de entrada
        self.entry_phone.delete(0, tk.END)
        self.entry_phone.insert(0, phone)
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, name)

        # Guardar el contacto seleccionado para futuras modificaciones
        self.selected_contact = {"telefono": phone, "nombre": name}

    def add_contact(self):
        """Agregar o editar un contacto"""
        # Obtener datos ingresados
        phone = self.entry_phone.get().strip()
        name = self.entry_name.get().strip()
        
        # Validar que ambos campos estén completos
        if not phone or not name:
            messagebox.showerror("Error", "Por favor ingresa el número de teléfono y el nombre.")
            return

        # Verificar si estamos editando un contacto o agregando uno nuevo
        if hasattr(self, 'selected_contact') and self.selected_contact:
            # Editar el contacto
            self.selected_contact["telefono"] = phone
            self.selected_contact["nombre"] = name
            self.update_contact_in_list()
        else:
            # Agregar un nuevo contacto
            new_contact = {"telefono": phone, "nombre": name}
            self.contacts_list.append(new_contact)
            self.save_contacts()
            self.contacts_tree.insert("", "end", values=(phone, name))
        
        # Limpiar los campos
        self.entry_phone.delete(0, tk.END)
        self.entry_name.delete(0, tk.END)

    def update_contact_in_list(self):
        """Actualizar el contacto en la lista y guardarlo en el archivo."""
        # Buscar el contacto en la lista y actualizar sus datos
        for idx, contact in enumerate(self.contacts_list):
            if contact["telefono"] == self.selected_contact["telefono"]:
                self.contacts_list[idx] = self.selected_contact
                break
        
        # Guardar la lista actualizada en el archivo
        self.save_contacts()

        # Actualizar la tabla de contactos
        self.refresh_contacts_tree()

        # Limpiar la selección de contacto
        del self.selected_contact

    def delete_contact(self):
        """Eliminar el contacto seleccionado y actualizar el archivo JSON."""
        # Obtener el contacto seleccionado
        selected_item = self.contacts_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Por favor selecciona un contacto para eliminar.")
            return

        # Obtener los datos del contacto seleccionado
        # phone = self.contacts_tree.item(selected_item)["values"][0]
        # print(phone)
        phone = str(self.contacts_tree.item(selected_item)["values"][0])  # Convertir a string

        # Confirmar la eliminación
        if not messagebox.askyesno("Confirmación", f"¿Estás seguro de que deseas eliminar el contacto {phone}?"):
            return

        # Eliminar el contacto de la lista de contactos
        self.contacts_list = [contact for contact in self.contacts_list if contact["telefono"] != phone]
        # print(self.contacts_list)
        # Guardar la lista actualizada en el archivo JSON
        self.save_contacts()  # Este método sobrescribe el archivo contactos.json
        

        # Eliminar el contacto de la tabla de la interfaz
        self.contacts_tree.delete(selected_item)


    def save_contacts(self):
        """Guardar la lista de contactos en contactos.json."""
        os.makedirs(os.path.dirname(self.contacts_file), exist_ok=True)
        with open(self.contacts_file, "w", encoding="utf-8") as f:
            json.dump(self.contacts_list, f, indent=4)


    def refresh_contacts_tree(self):
        """Actualizar la tabla de contactos con la lista actualizada."""
        # Limpiar la tabla actual
        for item in self.contacts_tree.get_children():
            self.contacts_tree.delete(item)

        # Llenar la tabla con los contactos actualizados
        for contact in self.contacts_list:
            self.contacts_tree.insert("", "end", values=(contact["telefono"], contact["nombre"]))

    def clear_main_area(self):
        """Función para limpiar el área principal"""
        for widget in self.main_area.winfo_children():
            widget.destroy()


    def pred_campaigns(self):
        self.clear_main_area()

        # Frame para contener los inputs
        input_frame = ttk.Frame(self.main_area)
        input_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

        # Input para el nombre de la campaña
        lbl_name = ttk.Label(input_frame, text="Título de la campaña")
        lbl_name.pack(anchor=tk.W)
        self.entry_name = ttk.Entry(input_frame)
        self.entry_name.pack(fill=tk.X, pady=5)

        # Input para la campaña
        lbl_campaign = ttk.Label(input_frame, text="Contenido de la campaña")
        lbl_campaign.pack(anchor=tk.W)
        self.text_campaign = tk.Text(input_frame, height=5)
        self.text_campaign.pack(fill=tk.X, pady=5)

        # Input para cargar una imagen
        self.btn_load_image = ttk.Button(input_frame, text="Cargar Imagen", command=self.load_image)
        self.btn_load_image.pack(pady=5)

        # Botón para eliminar campaña
        btn_delete = ttk.Button(input_frame, text="Eliminar Campaña", command=lambda: self.delete_campaign(campaign_type = "campaigns"))
        btn_delete.pack(pady=5)

        # Vista previa de la imagen
        self.image_preview = ttk.Label(input_frame)
        self.image_preview.pack(pady=10)

        # Botón de guardar
        btn_save = ttk.Button(input_frame, text="Guardar Campaña", command=lambda: self.save_campaign(campaign_type = "campaigns"))
        btn_save.pack(pady=20)

        # Tabla
        columns = ("Nombre de la Campaña",)
        self.tree = ttk.Treeview(self.main_area, columns=columns, show="headings")
        self.tree.heading("Nombre de la Campaña", text="Nombre de la Campaña")
        self.tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Cargar campañas existentes al iniciar
        self.load_campaigns(campaign_type = "campaigns")

        # Asociar evento de doble clic en la tabla
        self.tree.bind("<Double-1>", lambda event: self.on_double_click(event, campaign_type = "campaigns"))
        

    def dynamic_campaigns(self):
        self.clear_main_area()

        # Frame para contener los inputs
        input_frame = ttk.Frame(self.main_area)
        input_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

        # Input para el nombre de la campaña
        lbl_name = ttk.Label(input_frame, text="Título de la campaña")
        lbl_name.pack(anchor=tk.W)
        self.entry_name = ttk.Entry(input_frame)
        self.entry_name.pack(fill=tk.X, pady=5)

        # Input para la campaña
        lbl_campaign = ttk.Label(input_frame, text="Contenido de la campaña")
        lbl_campaign.pack(anchor=tk.W)
        self.text_campaign = tk.Text(input_frame, height=5)
        self.text_campaign.pack(fill=tk.X, pady=5)

        # Input para cargar una imagen
        self.btn_load_image = ttk.Button(input_frame, text="Cargar Imagen", command=self.load_image)
        self.btn_load_image.pack(pady=5)

        # Botón para eliminar campaña
        btn_delete = ttk.Button(input_frame, text="Eliminar Campaña", command=lambda: self.delete_campaign(campaign_type = "custom_campaign"))
        btn_delete.pack(pady=5)

        # Vista previa de la imagen
        self.image_preview = ttk.Label(input_frame)
        self.image_preview.pack(pady=10)

        # Botón de guardar
        btn_save = ttk.Button(input_frame, text="Guardar Campaña", command=lambda: self.save_campaign(campaign_type = "custom_campaign"))
        btn_save.pack(pady=20)

        # Tabla
        columns = ("Nombre de la Campaña",)
        self.tree = ttk.Treeview(self.main_area, columns=columns, show="headings")
        self.tree.heading("Nombre de la Campaña", text="Nombre de la Campaña")
        self.tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Cargar campañas existentes al iniciar
        self.load_campaigns(campaign_type = "custom_campaign")

        # Asociar evento de doble clic en la tabla
        self.tree.bind("<Double-1>", lambda event: self.on_double_click(event, campaign_type = "custom_campaign"))

    def send_messages(self):
        self.clear_main_area()
        
        # Frame para la configuración de envío de mensajes
        config_frame = ttk.Frame(self.main_area)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Etiqueta y entrada para la duración entre mensajes (en segundos)
        lbl_interval = ttk.Label(config_frame, text="Duración entre mensajes (segundos)")
        lbl_interval.grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.entry_interval = ttk.Entry(config_frame, width=30)  # Ajustamos el ancho del Entry
        self.entry_interval.grid(row=0, column=1, padx=10, pady=5)
        
        # Etiqueta y entrada para la pausa después de cierta cantidad de mensajes
        lbl_pause = ttk.Label(config_frame, text="Pausa después de mensajes enviados")
        lbl_pause.grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.entry_pause = ttk.Entry(config_frame, width=30)  # Ajustamos el ancho del Entry
        self.entry_pause.grid(row=1, column=1, padx=10, pady=5)

        # Etiqueta y lista para seleccionar tipo de campaña
        lbl_campaign_type = ttk.Label(config_frame, text="Seleccionar Tipo de Campaña")
        lbl_campaign_type.grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.combo_campaign_type = ttk.Combobox(config_frame, values=["Predeterminada", "Personalizada","Default"], width=27)  # Ajustamos el ancho del Combobox
        self.combo_campaign_type.grid(row=2, column=1, padx=10, pady=5)
        self.combo_campaign_type.bind("<<ComboboxSelected>>", self.on_campaign_type_selected)

        # Etiqueta y lista para seleccionar tipo de mensaje
        lbl_message_type = ttk.Label(config_frame, text="Seleccionar Tipo de Mensaje")
        lbl_message_type.grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        self.combo_message_type = ttk.Combobox(config_frame, values=["Simple", "Facturas","Anti Spam"], width=27)  # Ajustamos el ancho del Combobox
        self.combo_message_type.grid(row=3, column=1, padx=10, pady=5)
        self.combo_message_type.bind("<<ComboboxSelected>>", self.on_message_type_selected)

        # Selector de tipo de base
        self.lbl_base_type = ttk.Label(config_frame, text="Seleccionar Tipo de Base")
        self.lbl_base_type.grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        self.combo_base_type = ttk.Combobox(config_frame, values=["Original", "Con Intervalos"], width=27)
        self.combo_base_type.grid(row=4, column=1, padx=10, pady=5)
        self.combo_base_type.bind("<<ComboboxSelected>>", self.on_base_type_selected)
        self.lbl_base_type.grid_remove()
        self.combo_base_type.grid_remove()


        # Input de intervalo de contacto (número entero)
        self.lbl_contact_interval = ttk.Label(config_frame, text="Intervalo de Contacto")
        self.lbl_contact_interval.grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        self.entry_contact_interval = ttk.Entry(config_frame, width=30)
        self.entry_contact_interval.grid(row=5, column=1, padx=10, pady=5)
        self.lbl_contact_interval.grid_remove()
        self.entry_contact_interval.grid_remove()

        
        
        
        # Etiqueta y lista para seleccionar campañas guardadas
        self.lbl_campaign = ttk.Label(config_frame, text="Seleccionar Campaña")
        self.lbl_campaign.grid(row=6, column=0, sticky=tk.W, padx=10, pady=5)
        self.combo_campaign = ttk.Combobox(config_frame, values=self.get_campaign_titles(campaing_type="campaigns"), width=27)  # Ajustamos el ancho del Combobox
        self.combo_campaign.grid(row=6, column=1, padx=10, pady=5)
        self.lbl_campaign.grid_remove()
        self.combo_campaign.grid_remove()

        # Etiqueta y lista para seleccionar campañas personalizadas (inicialmente oculta)
        self.lbl_custom_campaign = ttk.Label(config_frame, text="Seleccionar Campaña Personalizada")
        self.lbl_custom_campaign.grid(row=7, column=0, sticky=tk.W, padx=10, pady=5)
        self.lbl_custom_campaign.grid_remove()

        self.combo_custom_campaign = ttk.Combobox(config_frame, values=self.get_campaign_titles(campaing_type="custom_campaign"), width=27)  # Ajustamos el ancho del Combobox
        self.combo_custom_campaign.grid(row=7, column=1, padx=10, pady=5)
        self.combo_custom_campaign.grid_remove()
        
        # Botón para cargar archivo de Excel
        self.btn_load_excel = ttk.Button(config_frame, text="Cargar Excel", command=self.load_excel_file)
        self.btn_load_excel.grid(row=8, column=0, padx=10, pady=10)

        # Botón para seleccionar carpeta (solo para "Facturas")
        self.btn_select_folder = ttk.Button(config_frame, text="Seleccionar Carpeta de Facturas", command=self.select_folder)
        self.btn_select_folder.grid(row=8, column=1, padx=10, pady=10)
        self.btn_select_folder.grid_remove()  # Ocultar inicialmente
        
        # Botones de enviar y cancelar
        self.btn_send = ttk.Button(config_frame, text="Enviar", command=self.validate_and_send)
        self.btn_send.grid(row=9, column=0, pady=10)
        
        self.btn_cancel = ttk.Button(config_frame, text="Cancelar", command=self.cancel_sending)
        self.btn_cancel.grid(row=9, column=1, pady=10)

        # Agregar una etiqueta para mostrar el contador de progreso
        self.lbl_progress = ttk.Label(config_frame, text="Progreso: 0/0")
        self.lbl_progress.grid(row=10, column=0, columnspan=2, pady=10)
        self.lbl_progress.grid_remove()  # Ocultar inicialmente


    def on_base_type_selected(self, event):
        """Muestra u oculta el campo de intervalo de contacto según el tipo de base seleccionado."""
        base_type = self.combo_base_type.get()
        if base_type == "Con Intervalos":
            self.entry_contact_interval.grid()
            self.lbl_contact_interval.grid()
        else:
            self.entry_contact_interval.grid_remove()
            self.lbl_contact_interval.grid_remove()

    
    
    # Función para generar un mensaje aleatorio
    def generar_mensaje_aleatorio(self):
        name = fake.first_name()
        tema = fake.word()
        fecha = fake.date()
        seccion = fake.word()
        
        saludo = random.choice(saludos).format(name=name)
        bienvenida = random.choice(mensajes_bienvenida)
        pregunta = random.choice(preguntas).format(tema=tema, seccion=seccion)
        recordatorio = random.choice(recordatorios).format(tema=tema, fecha=fecha, seccion=seccion)
        detalle = random.choice(detalles_recordatorio)
        sugerencia = random.choice(sugerencias).format(tema=tema, seccion=seccion)
        despedida = random.choice(despedidas).format(name=name)
        
        return f"{saludo} {bienvenida} {pregunta} {recordatorio} {detalle} {sugerencia} {despedida}"


    def load_contacts_from_json(self):
        # Cargar contactos adicionales desde contactos.json
        contacts_file = os.path.join(self.script_dir, "data/contactos.json")
        with open(contacts_file, "r") as file:
            contacts = json.load(file)
        return [contact["telefono"] for contact in contacts]

    def interpolate_contacts(self, original_list, contact_list, interval):
        # Interpolar contactos en la lista original cada 'interval' posiciones
        result = []
        contact_index = 0
        for i in range(len(original_list)):
            result.append(original_list[i])
            # Insertar un número de contacto cada intervalo
            if (i + 1) % interval == 0:
                result.append(contact_list[contact_index])
                contact_index = (contact_index + 1) % len(contact_list)  # Avanzar y repetir si necesario
        return result
    

##----------------------------------------------------------------------------------
    def on_campaign_type_selected(self, event):
        self.selected_type_campaign = self.combo_campaign_type.get()
        selected_type_campaign = self.selected_type_campaign
        if selected_type_campaign == "Personalizada":
            self.lbl_campaign.grid()
            self.combo_campaign.grid()
            self.combo_campaign.grid()
            self.btn_select_folder.grid()
            self.lbl_custom_campaign.grid()
            self.combo_custom_campaign.grid()
            # self.lbl_base_type.grid_remove()
            # self.combo_base_type.grid_remove()
            self.selected_folder = None
        elif selected_type_campaign == "Default":
            self.lbl_campaign.grid_remove()
            self.combo_custom_campaign.grid_remove()
            self.lbl_custom_campaign.grid_remove()
            self.selected_folder = None
            self.btn_select_folder.grid_remove()
            self.combo_campaign.grid_remove()
            # self.lbl_base_type.grid()
            # self.combo_base_type.grid()

        else:
            self.lbl_campaign.grid()
            self.combo_campaign.grid()
            self.combo_custom_campaign.grid_remove()
            self.lbl_custom_campaign.grid_remove()
            # self.lbl_base_type.grid_remove()
            # self.combo_base_type.grid_remove()
        self.selected_folder = None
        self.btn_select_folder.grid_remove()


    def on_message_type_selected(self, event):
        selected_type_message = self.combo_message_type.get()
        if selected_type_message == "Facturas":
            self.btn_select_folder.grid()
            self.lbl_base_type.grid_remove()
            self.combo_base_type.grid_remove()
            self.lbl_contact_interval.grid_remove()
            self.entry_contact_interval.grid_remove()
            # # Reubicar elementos originalmente
            # self.btn_load_excel.grid(row=5, column=0, padx=10, pady=10)
            # self.btn_select_folder.grid(row=5, column=1, padx=10, pady=10)
            # self.btn_send.grid(row=6, column=0, pady=10)
            # self.btn_cancel.grid(row=6, column=1, pady=10)

            # self.lbl_custom_campaign.grid_remove()
            
        elif selected_type_message == "Anti Spam":
            self.btn_select_folder.grid_remove()
            self.lbl_base_type.grid()
            self.combo_base_type.grid()
            self.selected_folder = None
        else:
            self.selected_folder = None
            self.lbl_base_type.grid_remove()
            self.combo_base_type.grid_remove()
            self.lbl_contact_interval.grid_remove()
            self.entry_contact_interval.grid_remove()
            # # Reubicar elementos originalmente
            # self.btn_load_excel.grid(row=5, column=0, padx=10, pady=10)
            # self.btn_select_folder.grid(row=5, column=1, padx=10, pady=10)
            # self.btn_send.grid(row=6, column=0, pady=10)
            # self.btn_cancel.grid(row=6, column=1, pady=10)

            # self.combo_custom_campaign.grid_remove()
            # self.lbl_custom_campaign.grid_remove()
            self.btn_select_folder.grid_remove()

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_folder = folder_selected
            # Mostrar mensaje de éxito 
            messagebox.showinfo("Carpeta Seleccionada", f"Carpeta {self.selected_folder} seleccionada correctamente.")

    def get_campaign_titles(self,campaing_type):
        # Función para obtener los títulos de las campañas desde el archivo JSON
        campaigns_file = os.path.join(self.script_dir, "data/campañas/"+campaing_type+".json")
        campaign_titles = []
        if os.path.exists(campaigns_file):
            with open(campaigns_file, "r") as f:
                campaigns_list = json.load(f)
            campaign_titles = [campaign["title"] for campaign in campaigns_list]
        return campaign_titles
    
    def cancel_sending(self):
        self.cancel_flag = True
        # self.clear_main_area()

    def replace_variables(self, text_template, variables, default_campaign):
        # Expresión regular para encontrar las variables delimitadas por corchetes
        pattern = re.compile(r'\[(.*?)\]')
        
        # Función para reemplazar las variables con sus valores
        def replacer(match):
            variable_name = match.group(1)
            return str(variables.get(variable_name, f"[{variable_name}]"))
        
        # Reemplazar las variables en el texto
        result_text = pattern.sub(replacer, text_template)

        # Verificación: si algún valor no se reemplazó correctamente, retornar la campaña predeterminada
        for variable_name, valor in variables.items():
            if str(valor).lower() == 'nan' or valor is None or (isinstance(valor, float) and np.isnan(valor)):
                # print(f"Valor faltante para la variable [{variable_name}], enviando campaña predeterminada.")
                return default_campaign

        return result_text
    
    def generate_message_for_phone(self, phone_number, text_template,default_campaign):
        # Buscar los datos del usuario por número de teléfono
        user_data = self.user_data_by_phone.get(phone_number)
        if user_data is None:
            raise ValueError(f"No se encontraron datos para el número de teléfono: {phone_number}")
        
        # Generar el mensaje reemplazando las variables en el texto
        return self.replace_variables(text_template, user_data,default_campaign)

    def load_excel_file(self):
        # Función para cargar un archivo de Excel y procesar los números de celular
        self.file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if self.file_path:
            try:
                # Leer el archivo de Excel y obtener los números de teléfono
                df = pd.read_excel(self.file_path)
                #self.phone_numbers = df['Celular'].tolist()  # Asumiendo que la columna de números se llama 'Telefono'
                
                 # Verificar si la columna 'Celular' existe
                if 'Celular' not in df.columns:
                    raise ValueError("El archivo Excel debe contener una columna 'Celular'")
                
                # Obtener la lista de números de teléfono
                self.phone_numbers = df['Celular'].tolist()
                
                # Crear un diccionario para almacenar los datos de usuario por número de teléfono
                self.user_data_by_phone = {}
                self.contact_data_by_phone = {}
                
                for _, row in df.iterrows():
                    phone_number = row['Celular']
                    user_data = row.drop(labels=['Celular']).to_dict()
                    
                    # Filtrar y almacenar las columnas que contienen la palabra "Contacto"
                    # Filtrar y almacenar las columnas que contienen la palabra "Contacto"
                    contact_data = {k: int(v) for k, v in user_data.items() if 'Contacto' in k and pd.notna(v)}
                    non_contact_data = {k: v for k, v in user_data.items() if 'Contacto' not in k}
                    
                    self.user_data_by_phone[phone_number] = non_contact_data
                    self.contact_data_by_phone[phone_number] = contact_data
                #print(self.contact_data_by_phone["3217166019"])
                
                # Mostrar mensaje de éxito y almacenar los números en una variable de instancia
                messagebox.showinfo("Archivo Cargado", f"Archivo {self.file_path} cargado correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo de Excel: {e}")
                self.phone_numbers = []  # Asignar una lista vacía en caso de error
                self.user_data_by_phone = {}
                self.contact_data_by_phone = {}
                self.file_path = None


    def send_message(self, phone, message, image_path=None, interval=0):
        # print(f"Enviando mensaje a {phone}...")
        global informe

        informe_aux = {}
        # Captura el tiempo antes del proceso
        start_time = time.time()
        
        try:
            # Ejecutar JavaScript para hacer clic en el botón "Nuevo chat"
            time.sleep(1)
            try:
                nuevo_chat_btn = self.driver.find_element(
                    By.CSS_SELECTOR, "[title='Nuevo chat'], [aria-label='Nuevo chat']"
                )
                nuevo_chat_btn.click()
            except:
                # 2) Buscar el span con el icono y subir al botón
                btn_icon = self.driver.find_element(
                    By.XPATH,
                    "//span[@data-icon='new-chat-outline']/ancestor::button[1]"
                )
                btn_icon.click()

            # Esperar hasta que el campo de búsqueda esté disponible para escribir
            time.sleep(0.5)
            input_field = self.wait.until(EC.presence_of_element_located((By.XPATH, '//p[@class="selectable-text copyable-text x15bjb6t x1n2onr6"]')))
            contacts = self.contact_data_by_phone.get(phone, {})
            phone = [phone]
            if contacts is not None and contacts:
                # Convertir los valores del diccionario en una lista y agregarlos a phone
                # Filtrar los valores vacíos o NaN y obtener solo los valores válidos
                valid_contacts = {k: v for k, v in contacts.items() if v is not None and not (isinstance(v, float) and np.isnan(v))}
                # Convertir valid_contacts en una lista si es necesario
                phone_numbers = list(valid_contacts.values())
                phone.extend(phone_numbers)
                
            for index, number in enumerate(phone):
                # Limpiar el campo de búsqueda
                time.sleep(0.5)
                input_field.send_keys(Keys.CONTROL + "a")
                time.sleep(0.5)
                input_field.send_keys(Keys.DELETE)
                # Buscar contacto
                time.sleep(0.5)
                input_field.send_keys(number)
                time.sleep(1)
                # input_field.send_keys(Keys.ENTER)
                #parent_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.x1n2onr6.x1n2onr6.xyw6214.x78zum5.x1r8uery.x1iyjqo2.xdt5ytf.x6ikm8r.x1odjw0f.x1hc1fzr.x150wa6m')))
                parent_element = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x1y332i5') and contains(@class, 'x1n2onr6')]")))
                try:
                    # Localizar el nuevo elemento hijo (div) dentro del elemento padre
                    time.sleep(1)
                    specific_element = parent_element.find_element(By.CSS_SELECTOR, 'div.x1c436fg')
                    #<div class="x1c436fg">No se pudo establecer la conexión a Internet.</div>
                    #print("SIN CONEXION A INTERNET")
                    back_button = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@role="button" and @aria-label="Atrás"]'))
                    )
                    
                    # Haz clic en el elemento
                    back_button.click()
                    #print('Click atras')
                    while True:
                        time.sleep(10)
                        try:
                            # Espera hasta que el elemento padre esté presente
                            
                            parent_element = self.wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, 'div._amiu._amil'))
                            )
                            # Encuentra el botón "Reconectar" dentro del elemento padre
                            #print("si se encontro el recuadro de reconectar")
                            reconnect_button = parent_element.find_element(By.XPATH, './/button[.//span[text()="Reconectar"]]')

                            # Haz clic en el botón "Reconectar"
                            reconnect_button.click()
                        except:
                            break
                    #print("reconectado")
                    
                except:
                    try:
                        time.sleep(2)
                        # Busca cualquiera de los dos textos dentro del span
                        span = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((
                                By.XPATH, "//span[contains(text(), 'Contactos en WhatsApp') or contains(text(), 'Usuarios que no están en tus contactos')]"
                            ))
                        )
                    except:
                        #print("Sin Whatsapp")
                        # Espera hasta que el elemento span con data-icon="back" esté presente y visible
                        informe_aux = {"Numero":phone[0],"Estado":"Sin whatsapp"}
                        if index != len(phone) - 1:
                            continue
                        back_button = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//div[@role="button" and @aria-label="Atrás"]'))
                        )
                        
                        # Haz clic en el elemento
                        back_button.click()
                        #print('Click atras')
                        time.sleep(1)
                    else:
                        # Esperar un poco para que el chat cargue
                        time.sleep(0.5)
                        input_field.send_keys(Keys.ENTER)
                        time.sleep(0.5)
                        # Esperar hasta que el elemento padre específico esté presente
                        parent = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div._ak1q')))

                        # Añadir una pequeña espera para asegurar que el contenido esté completamente cargado
                        time.sleep(1.5)

                        # Luego encontrar el hijo específico dentro de ese padre
                        child = parent.find_element(By.CSS_SELECTOR, 'p.selectable-text.copyable-text.x15bjb6t.x1n2onr6')
                        time.sleep(0.8)

                        # Hacer algo con el elemento hijo (por ejemplo, enviar un mensaje)
                        # child.click()  # Si necesitas hacer clic en el elemento antes de enviar texto
                        # time.sleep(0.5)
                        # child.send_keys(message)
                        # Enviar mensaje con múltiples párrafos
                        # print(message)
                        time.sleep(0.5)
                        child.send_keys(Keys.CONTROL + "a")
                        time.sleep(0.5)
                        child.send_keys(Keys.DELETE)
                        paragraphs = message.split('\n')  # Dividir el mensaje en párrafos
                        for paragraph in paragraphs:
                            child.send_keys(paragraph)
                            child.send_keys(Keys.SHIFT + Keys.ENTER)
                        time.sleep(0.5)
                        # child.send_keys(Keys.ENTER)
                        
                        # Si hay una imagen a enviar
                        if image_path and os.path.isfile(image_path):
                            # print('Hay una imagen a enviar')
                            # Hacer clic en el botón de adjuntar archivos (clip icon)
                            try:
                                adjuntar_btn = self.driver.find_element(
                                    By.CSS_SELECTOR, "[title='Adjuntar'], [aria-label='Adjuntar']"
                                )
                                time.sleep(0.5)
                                adjuntar_btn.click()
                            except:
                                adjuntar_btn = self.driver.find_element(
                                    By.XPATH,
                                    "//span[@data-icon='plus-rounded']/ancestor::button[1]"
                                )
                                adjuntar_btn.click()



                            # 1. Localizar el span
                            span = self.driver.find_element(By.XPATH, '//span[text()="Fotos y videos"]')

                            # 2. Obtener padres
                            parents = [span]
                            current = span

                            for i in range(1, 6):
                                current = current.find_element(By.XPATH, './..')
                                parents.append(current)

                            print("Total elementos a probar:", len(parents))

                            # 3. Probar click en cada nodo
                            for idx, elem in enumerate(parents):
                                print(f"\n====== Probando CLICK en elemento {idx} ======")
                                print("Tag:", elem.tag_name)

                                # --- AÑADIR HANDLER SOLO AL ELEMENTO ACTUAL (SIN CAPTURA) ---
                                #self.driver.execute_script("""
                                #    arguments[0]._temp_handler = function(e) {
                                #        e.preventDefault();     // ✔ evita abrir la ventana
                                #        e.stopImmediatePropagation(); // ✔ evita subir a padres
                                #    };
                                #    arguments[0].addEventListener('click', arguments[0]._temp_handler, false);
                                #""", elem)

                                time.sleep(0.3)

                                # CLICK
                                try:
                                    elem.click()
                                except:
                                    try:
                                        self.driver.execute_script("arguments[0].click();", elem)
                                    except:
                                        print("❌ No se pudo hacer click")

                                time.sleep(1)

                                # VER INPUTS
                                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                                print("Total inputs file encontrados:", len(inputs))

                                for i, inp in enumerate(inputs):
                                    print(f"\n======= INPUT {i} =======")
                                    print(f"type: {inp.get_attribute('type')}")
                                    print(f"name: {inp.get_attribute('name')}")
                                    print(f"id: {inp.get_attribute('id')}")
                                    print("HTML completo:")
                                    print(inp.get_attribute("outerHTML"))
                                    print("=========================\n")

                                # --- REMOVER HANDLER ---
                                self.driver.execute_script("""
                                    arguments[0].removeEventListener('click', arguments[0]._temp_handler, false);
                                    arguments[0]._temp_handler = null;
                                """, elem)
                                #body = driver.find_element(By.TAG_NAME, "body")
                                #body.send_keys(Keys.ESCAPE)
                                print("============================================")



                            # Hacer clic en el botón de "Fotos y videos"
                            print("buscando el padre 1")
                            try:
                                element = WebDriverWait(self.driver, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, "//li[.//span[text()='Fotos y videos']]"))
                                )
                                print("padre 1 encontrado")
                            except:
                                try:
                                    print("buscando el padre 2")
                                    element = WebDriverWait(self.driver, 10).until(
                                        EC.presence_of_element_located((By.XPATH, '//span[text()="Fotos y videos"]/ancestor::li[1]'))
                                    )
                                    print("padre 2 encontrado")
                                except:
                                    try:
                                        print("buscando el padre 3")
                                        element = self.driver.find_element(
                                            By.XPATH,
                                            "//span[contains(text(), 'Fotos y videos')]/ancestor::li[1]"
                                        )
                                        #element.click()
                                        print("padre 3 encontrado")
                                    except:
                                        print("buscando el padre 4")
                                        element = self.driver.find_element(
                                            By.XPATH,
                                            "//span[@data-icon='media-filled-refreshed']/ancestor::li[1]"
                                        )
                                        #element.click()
                                        print("padre 4 encontrado")


                            # Acceder al elemento padre del input
                            #time.sleep(0.5)
                            #parent_element = element.find_element(By.XPATH, './..')
                            time.sleep(0.5)
                            #file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                            #print("file_input encontrado")
                            #file_input.send_keys(image_path)
                            # Bloquea que se abra la ventana
                            # Evitar que se abra el file picker pero permitir que React cree el input

                            #for i, inp in enumerate(inputs):
                            #    print(f"{i}: type='{inp.get_attribute('type')}', name='{inp.get_attribute('name')}', id='{inp.get_attribute('id')}'")
                            #inputs[1].send_keys(image_path)
                            #pyautogui.press('esc')
                            # Obtener el input dentro del elemento padre
                            #file_input = parent_element.find_element(By.CSS_SELECTOR, 'input[type="file"]')
                            #time.sleep(0.5)
                            #file_input.send_keys(image_path)
                            print("pasa4")
                            time.sleep(1)
                            send_button = WebDriverWait(self.driver, 60).until(
                                EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Enviar"]'))
                                
                            )
                            time.sleep(0.5)
                            send_button.click()
                            
                        else:
                            child.send_keys(Keys.ENTER)
                        # Hacer clic en el botón
                        # send_button.click()
                        time.sleep(1)
                        self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                        informe_aux = {"Numero":phone[0],"Estado":"Enviado"}
                        # Captura el tiempo después del proceso
                        end_time = time.time()
                        # Calcula el tiempo transcurrido
                        elapsed_time = end_time - start_time
                        pause = max(0, interval - elapsed_time)
                        if (self.cancel_flag):
                            pause = 0
                        time.sleep(pause)
                        break

            informe.append(informe_aux)  
        except Exception as e:
            print(f"Error al procesar: {e}")
        time.sleep(1)


    def validate_and_send(self):
        self.cancel_flag = False
        # Función para validar la carga del archivo Excel y los datos del menú de configuración
        self.interval = self.entry_interval.get()
        self.pause = self.entry_pause.get()
        self.campaign_title = self.combo_campaign.get()
        self.message_type = self.combo_message_type.get()
        self.campaign_type = self.combo_campaign_type.get()
        
        # Validar la carga del archivo Excel
        if not self.file_path:  # Verificar si self.file_path tiene valor
            messagebox.showerror("Error", "Por favor carga un archivo de Excel.")
            return
        
        if self.message_type == "Facturas" and not self.selected_folder:
            messagebox.showwarning("Advertencia", "Debe seleccionar una carpeta para las facturas.")
            return

        # Validación de tipo de base
        if self.message_type == "Anti Spam" and not self.combo_base_type.get():
            messagebox.showerror("Error", "Por favor selecciona un tipo de base.")
            return 
        
        # Validación de intervalo de contacto solo si es "Con Intervalos"
        if self.message_type == "Anti Spam" and self.combo_base_type.get() == "Con Intervalos":
            if not self.entry_contact_interval.get().isdigit() or int(self.entry_contact_interval.get()) <= 0:
                messagebox.showerror("Error", "Por favor ingresa un intervalo de contacto válido.")
                return
        # Validar que todos los campos estén completos en el menú de configuración
        if not self.interval or not self.pause or not self.message_type or not self.campaign_type:
            messagebox.showerror("Error", "Por favor completa todos los campos en el menú de configuración.")
            return

        if self.campaign_type != "Default":
            if not self.campaign_title:
                messagebox.showerror("Error", "Por favor selecciona una campaña.")
                return

        # Validar que interval y pause sean números enteros
        if not self.interval.isdigit() or not self.pause.isdigit():
            messagebox.showerror("Error", "Por favor ingresa valores numéricos válidos para la duración y la pausa.")
            return
        
        if self.combo_campaign_type.get() == "Personalizada":
            if not self.combo_custom_campaign.get():
                messagebox.showerror("Error", "Debe seleccionar una campaña personalizada.")
                return

        # Convertir interval y pause a enteros
        self.interval = int(self.interval)
        self.pause = int(self.pause)
        # Validar que interval sea mayor a 20 segundos
        # Validación de intervalo de contacto solo si es "Con Intervalos"

        if self.message_type == "Anti Spam" and self.combo_base_type.get() == "Con Intervalos":
            # print(self.message_type == "Anti Spam")
            # print(self.combo_base_type.get() == "Con Intervalos")
            if self.interval < 30:
                # print(self.combo_base_type.get() == "Con Intervalos")
                messagebox.showerror("Error", "Por favor ingresa una duracion de envio entre mensajes mayor a 30 segundos.")
                return

        if self.interval < 20:
            messagebox.showerror("Error", "Por favor ingresa un intervalo mayor a 20 segundos.")
            return

        # Crear una instancia del navegador Selenium
        self.interval = self.interval

        try:
            if not self.driver:
                self.driver = webdriver.Chrome(service=self.service)
                self.wait = WebDriverWait(self.driver, 60)
                # Alerta al iniciar el navegador
                self.driver.get('https://web.whatsapp.com')
                
                # Aquí puedes agregar validaciones si es necesario antes de iniciar el hilo
                
            while True:
                    if not messagebox.askokcancel("Alerta", "Por favor inicie sesión en WhatsApp y presione continuar."):
                        self.driver.quit()
                        self.driver = None
                        return
                    # Verificar si el elemento "Nuevo chat" está presente
                    try:
                        # WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[title='Nuevo chat']")))
                        # Esperar que el botón esté presente
                        try:
                            nuevo_chat_btn = self.driver.find_element(
                                By.CSS_SELECTOR, "[title='Nuevo chat'], [aria-label='Nuevo chat']"
                            )
                            nuevo_chat_btn.click()
                        except:
                            # 2) Buscar el span con el icono y subir al botón
                            btn_icon = self.driver.find_element(
                                By.XPATH,
                                "//span[@data-icon='new-chat-outline']/ancestor::button[1]"
                            )
                            btn_icon.click()
                        self.lbl_progress.grid()
                        break  # Salir del bucle si el elemento está presente
                    except:
                        # Si el elemento no está presente, mostrar la alerta nuevamente
                        #try:
                        #    WebDriverWait(self.driver, 10).until(
                        #            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[aria-label='Nuevo chat'][role='button']"))
                        #        )
                        #    break
                        #except:
                            #continue
                        time.sleep(2)
                        continue
            global informe
            informe = []
            # print("antes de tread")
            threading.Thread(target=self.send_messages_in_thread, args=(self.campaign_title, self.message_type, self.pause, self.interval, self.campaign_type)).start()   
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el navegador: {e}")
            return
        

    def verificar_archivo_pdf(self, ruta, nombre_archivo):
        # Asegurarse de que el nombre del archivo incluye la extensión .pdf
        if not nombre_archivo.endswith('.pdf'):
            return ""

        # Combinar la ruta y el nombre del archivo para obtener la ruta completa del archivo
        ruta_completa = os.path.join(ruta, nombre_archivo)
        
        # Verificar si el archivo existe y si es un archivo regular
        if os.path.isfile(ruta_completa):
            return ruta_completa
        else:
            return ""
        
    def send_messages_in_thread(self, campaign_title, message_type, pause_after, interval,campaign_type):
        # Obtener los datos de la campaña seleccionada
    
        campaign_pred = self.get_campaign_data(campaign_title, campaign_type = "campaigns")
        # print(campaign_pred)
        if campaign_type == "Personalizada":
            campaign_data = self.get_campaign_data(self.combo_custom_campaign.get(), campaign_type = "custom_campaign")
            # print(campaign_data)
        else:
            campaign_data = campaign_pred

        if campaign_data or campaign_type == "Default":
            if campaign_type == "Default":
                message = ""
                campaign_image = ""
            else:
                message = campaign_data["message"]
                campaign_image = campaign_data["image"]

            try:
                if message_type == "Simple":
                    for index, phone_number in enumerate(self.phone_numbers):
                        if self.cancel_flag:
                            # messagebox.showinfo("Cancelado", "El envío de mensajes ha sido cancelado.")
                            # # Convertir la lista de diccionarios en un DataFrame
                            df = pd.DataFrame(informe)
                            # Obtener la fecha y hora actual
                            now = datetime.now()
                            # Formatear la fecha y hora para usar en el nombre del archivo
                            fecha_formateada = now.strftime("%Y%m%d_%H%M%S")
                            # Crear el nombre del archivo
                            nombre_archivo = f"Informe_{fecha_formateada}.xlsx"
                            # Crear la ruta completa para la carpeta "informes"
                            ruta_informes = os.path.join(self.script_dir, "informes")

                            # Crear la carpeta "informes" si no existe
                            os.makedirs(ruta_informes, exist_ok=True)

                            # Crear la ruta completa para el archivo Excel
                            ruta_archivo = os.path.join(ruta_informes, nombre_archivo)

                            # Guardar el DataFrame en un archivo Excel con la ruta generada
                            df.to_excel(ruta_archivo, index=False)
                            messagebox.showinfo("Éxito", f"El envio ha sido cancelado,se guardo el informe en:{ruta_archivo}")
                            return
                        # Aquí deberías implementar la lógica para enviar mensajes a cada número de teléfono
                        # Usando los datos de intervalo, pausa, campaña y tipo de mensaje configurados
                        # y los datos cargados desde el archivo de Excel
                        if campaign_type == "Personalizada":
                            try:
                                campaign_message = self.generate_message_for_phone(phone_number, message,campaign_pred["message"])
                            except:
                                campaign_message = campaign_pred["message"]
                                campaign_image = campaign_pred["image"]
                        elif campaign_type == "Default":
                            campaign_message = self.generar_mensaje_aleatorio()
                            campaign_image = ""
                        else:
                            campaign_message = message
                        self.send_message(phone_number, campaign_message, image_path=campaign_image, interval=interval)
                        #time.sleep(interval)
                        if index > 0 and (index + 1) % pause_after == 0:
                            time.sleep(60)  # Pausa después de enviar un número específico de mensajes
                        # Actualiza el contador de progreso
                        self.lbl_progress.config(text=f"Progreso: {index + 1}/{len(self.phone_numbers)}")
                        
                        # Actualiza la interfaz gráfica para mostrar los cambios
                        self.update_idletasks()  # Necesario para actualizar la interfaz gráfica
                elif message_type == "Facturas":
                    selected_folder = self.selected_folder
                    for index, phone_number in enumerate(self.phone_numbers):
                        if self.cancel_flag:
                            df = pd.DataFrame(informe)
                            # Obtener la fecha y hora actual
                            now = datetime.now()
                            # Formatear la fecha y hora para usar en el nombre del archivo
                            fecha_formateada = now.strftime("%Y%m%d_%H%M%S")
                            # Crear el nombre del archivo
                            nombre_archivo = f"Informe_{fecha_formateada}.xlsx"
                            # Crear la ruta completa para la carpeta "informes"
                            ruta_informes = os.path.join(self.script_dir, "informes")

                            # Crear la carpeta "informes" si no existe
                            os.makedirs(ruta_informes, exist_ok=True)

                            # Crear la ruta completa para el archivo Excel
                            ruta_archivo = os.path.join(ruta_informes, nombre_archivo)

                            # Guardar el DataFrame en un archivo Excel con la ruta generada
                            df.to_excel(ruta_archivo, index=False)
                            messagebox.showinfo("Éxito", f"El envio ha sido cancelado,se guardo el informe en:{ruta_archivo}")
                            return
                        # Aquí deberías implementar la lógica para enviar mensajes a cada número de teléfono
                        # Usando los datos de intervalo, pausa, campaña y tipo de mensaje configurados
                        # y los datos cargados desde el archivo de Excel
                        # Combinar la ruta y el nombre del archivo para obtener la ruta completa del archivo
                        if campaign_type == "Personalizada":
                            try:
                                campaign_message = self.generate_message_for_phone(phone_number, message,campaign_pred["message"])
                            except:
                                campaign_message = campaign_pred["message"]
                                campaign_image = campaign_pred["image"]
                        elif campaign_type == "Default":
                            campaign_message = self.generar_mensaje_aleatorio()
                            campaign_image = ""
                        else:
                            campaign_message = message
                        
                        document_path = self.verificar_archivo_pdf(selected_folder, str(phone_number) + ".pdf")
                        if document_path != "":
                            self.send_message(phone_number, campaign_message, image_path=document_path, interval=interval)
                        #time.sleep(interval)
                        if index > 0 and (index + 1) % pause_after == 0:
                            time.sleep(60)  # Pausa después de enviar un número específico de mensajes
                        # Actualiza el contador de progreso
                        self.lbl_progress.config(text=f"Progreso: {index + 1}/{len(self.phone_numbers)}")
                        
                        # Actualiza la interfaz gráfica para mostrar los cambios
                        self.update_idletasks()  # Necesario para actualizar la interfaz gráfica
                    # print("")
                elif message_type == "Anti Spam":
                    min_value = 30
                    max_value = int(self.entry_interval.get())
                    interval = random.randint(min_value, max_value)
                    # pausa = int(self.entry_pause_after_send.get())

                    # Cargar la lista de números desde el archivo de Excel
                    phone_numbers = self.phone_numbers  # Esta lista se carga en la función `load_excel_file`

                    # Obtener el tipo de base y el intervalo de contacto
                    base_type = self.combo_base_type.get()

                    if base_type == "Con Intervalos":
                        # Cargar contactos adicionales desde contactos.json
                        contact_interval = int(self.entry_contact_interval.get())
                        contact_list = self.load_contacts_from_json()
                        
                        # Si la lista de contactos es menor que la original, repetimos los contactos
                        extended_contact_list = []
                        while len(extended_contact_list) < len(phone_numbers):
                            extended_contact_list.extend(contact_list)
                        
                        # Interpolar la lista de contactos en la lista original
                        phone_numbers = self.interpolate_contacts(phone_numbers, extended_contact_list, contact_interval)

                    for index, phone_number in enumerate(phone_numbers):
                        if self.cancel_flag:
                            # messagebox.showinfo("Cancelado", "El envío de mensajes ha sido cancelado.")
                            # # Convertir la lista de diccionarios en un DataFrame
                            df = pd.DataFrame(informe)
                            # Obtener la fecha y hora actual
                            now = datetime.now()
                            # Formatear la fecha y hora para usar en el nombre del archivo
                            fecha_formateada = now.strftime("%Y%m%d_%H%M%S")
                            # Crear el nombre del archivo
                            nombre_archivo = f"Informe_{fecha_formateada}.xlsx"
                            # Crear la ruta completa para la carpeta "informes"
                            ruta_informes = os.path.join(self.script_dir, "informes")

                            # Crear la carpeta "informes" si no existe
                            os.makedirs(ruta_informes, exist_ok=True)

                            # Crear la ruta completa para el archivo Excel
                            ruta_archivo = os.path.join(ruta_informes, nombre_archivo)

                            # Guardar el DataFrame en un archivo Excel con la ruta generada
                            df.to_excel(ruta_archivo, index=False)
                            messagebox.showinfo("Éxito", f"El envio ha sido cancelado,se guardo el informe en:{ruta_archivo}")
                            return
                        # Aquí deberías implementar la lógica para enviar mensajes a cada número de teléfono
                        # Usando los datos de intervalo, pausa, campaña y tipo de mensaje configurados
                        # y los datos cargados desde el archivo de Excel
                        if campaign_type == "Personalizada":
                            try:
                                campaign_message = self.generate_message_for_phone(phone_number, message,campaign_pred["message"])
                            except:
                                campaign_message = campaign_pred["message"]
                                campaign_image = campaign_pred["image"]
                        elif campaign_type == "Default":
                            campaign_message = self.generar_mensaje_aleatorio()
                            campaign_image = ""
                        else:
                            campaign_message = message

                        self.send_message(phone_number, campaign_message, image_path=campaign_image, interval=interval)
                        #time.sleep(interval)
                        if index > 0 and (index + 1) % pause_after == 0:
                            time.sleep(120)  # Pausa después de enviar un número específico de mensajes
                        # Actualiza el contador de progreso
                        self.lbl_progress.config(text=f"Progreso: {index + 1}/{len(self.phone_numbers)}")
                        
                        # Actualiza la interfaz gráfica para mostrar los cambios
                        self.update_idletasks()  # Necesario para actualizar la interfaz gráfica
                # Extraer todos los números del informe a una lista
                # print(informe)
                #numeros_informe = [entry["Numero"] for entry in informe]
                # Extraer todos los números del informe a una lista, ignorando objetos vacíos o sin el atributo "Numero"
                numeros_informe = [entry["Numero"] for entry in informe if "Numero" in entry]

                # print(numeros_informe)

                # Convertir las listas a conjuntos para facilitar la comparación
                set_phone_numbers = set(self.phone_numbers)
                set_numeros_informe = set(numeros_informe)

                # Encontrar los números que están en self.phone_numbers pero no en el informe
                numeros_no_en_informe = set_phone_numbers - set_numeros_informe

                # Convertir el resultado a una lista (si prefieres trabajar con listas)
                numeros_no_en_informe = list(numeros_no_en_informe)

                # Verificar si la lista numeros_no_en_informe está vacía
                if len(numeros_no_en_informe) == 0:
                    # Convertir la lista de diccionarios en un DataFrame
                    df = pd.DataFrame(informe)
                    # Obtener la fecha y hora actual
                    now = datetime.now()
                    # Formatear la fecha y hora para usar en el nombre del archivo
                    fecha_formateada = now.strftime("%Y%m%d_%H%M%S")
                    # Crear el nombre del archivo
                    nombre_archivo = f"Informe_{fecha_formateada}.xlsx"
                    # Crear la ruta completa para la carpeta "informes"
                    ruta_informes = os.path.join(self.script_dir, "informes")

                    # Crear la carpeta "informes" si no existe
                    os.makedirs(ruta_informes, exist_ok=True)

                    # Crear la ruta completa para el archivo Excel
                    ruta_archivo = os.path.join(ruta_informes, nombre_archivo)

                    # Guardar el DataFrame en un archivo Excel con la ruta generada
                    df.to_excel(ruta_archivo, index=False)
                    messagebox.showinfo("Éxito", f"El envio ha finalizado,se guardo el informe en:{ruta_archivo}")
                else:
                    # Si la lista no está vacía, mostrar una alerta al usuario
                    cantidad_no_enviados = len(numeros_no_en_informe)
                    respuesta = messagebox.askyesno(
                        "Mensajes no enviados",
                        f"{cantidad_no_enviados} mensajes no se enviaron correctamente. ¿Desea reenviarlos?"
                    )

                    if respuesta:
                        print("Reenviando mensajes no enviados...")
                        self.phone_numbers = numeros_no_en_informe
                        # Llamar directamente a la función de envío de mensajes en el mismo hilo
                        self.send_messages_in_thread(
                            self.campaign_title, 
                            self.message_type, 
                            self.pause, 
                            self.interval, 
                            self.campaign_type
                        )
                    else:
                        # Convertir la lista de diccionarios en un DataFrame
                        df = pd.DataFrame(informe)
                        # Obtener la fecha y hora actual
                        now = datetime.now()
                        # Formatear la fecha y hora para usar en el nombre del archivo
                        fecha_formateada = now.strftime("%Y%m%d_%H%M%S")
                        # Crear el nombre del archivo
                        nombre_archivo = f"Informe_{fecha_formateada}.xlsx"
                        # Crear la ruta completa para la carpeta "informes"
                        ruta_informes = os.path.join(self.script_dir, "informes")

                        # Crear la carpeta "informes" si no existe
                        os.makedirs(ruta_informes, exist_ok=True)

                        # Crear la ruta completa para el archivo Excel
                        ruta_archivo = os.path.join(ruta_informes, nombre_archivo)

                        # Guardar el DataFrame en un archivo Excel con la ruta generada
                        df.to_excel(ruta_archivo, index=False)
                        messagebox.showinfo("Éxito", f"El envio ha finalizado,se guardo el informe en:{ruta_archivo}")

                
            except Exception as e:
                # messagebox.showerror("Error", f"Error al enviar mensajes: {e}")   
                # Convertir la lista de diccionarios en un DataFrame
                df = pd.DataFrame(informe)
                # Obtener la fecha y hora actual
                now = datetime.now()
                # Formatear la fecha y hora para usar en el nombre del archivo
                fecha_formateada = now.strftime("%Y%m%d_%H%M%S")
                # Crear el nombre del archivo
                nombre_archivo = f"Informe_{fecha_formateada}.xlsx"
                # Crear la ruta completa para la carpeta "informes"
                ruta_informes = os.path.join(self.script_dir, "informes")

                # Crear la carpeta "informes" si no existe
                os.makedirs(ruta_informes, exist_ok=True)

                # Crear la ruta completa para el archivo Excel
                ruta_archivo = os.path.join(ruta_informes, nombre_archivo)

                # Guardar el DataFrame en un archivo Excel con la ruta generada
                df.to_excel(ruta_archivo, index=False)
                messagebox.showerror("Error", f"Error al enviar mensajes: {e},se guardo el informe en:{ruta_archivo}")  
                if self.driver:
                    self.driver.quit()
                    self.driver = None


    def get_campaign_data(self, campaign_title, campaign_type):
        # Función para obtener los datos de una campaña desde el archivo JSON
        campaigns_file = os.path.join(self.script_dir, "data/campañas/"+campaign_type+".json")
        if os.path.exists(campaigns_file):
            with open(campaigns_file, "r") as f:
                campaigns_list = json.load(f)
                for campaign in campaigns_list:
                    if campaign["title"] == campaign_title:
                        return campaign
        return None


    def clear_main_area(self):
        # Función para limpiar el área principal
        for widget in self.main_area.winfo_children():
            widget.destroy()

    def load_campaigns(self, campaign_type):
        # Función para cargar las campañas guardadas en la tabla
        campaigns_file = os.path.join(self.script_dir, "data/campañas/"+campaign_type+".json")
        if os.path.exists(campaigns_file):
            with open(campaigns_file, "r",) as f:
                campaigns_list = json.load(f)
                for campaign in campaigns_list:
                    self.tree.insert("", "end", values=(campaign["title"],))

    def on_double_click(self, event, campaign_type):
        # Función para manejar el doble clic en una campaña y cargar sus datos
        item = self.tree.selection()[0]
        campaign_title = self.tree.item(item, "values")[0]
        campaigns_file = os.path.join(self.script_dir, "data/campañas/"+campaign_type+".json")
        
        if os.path.exists(campaigns_file):
            with open(campaigns_file, "r", encoding="utf-8") as f:
                campaigns_list = json.load(f)
                for campaign in campaigns_list:
                    if campaign["title"] == campaign_title:
                        self.entry_name.delete(0, tk.END)
                        self.entry_name.insert(0, campaign["title"])
                        self.text_campaign.delete(1.0, tk.END)
                        self.text_campaign.insert(1.0, campaign["message"])
                        self.load_image_preview(campaign["image"])
                        break
    # def delete_image(self):
    #     self.image_path = ""
    #     self.image_preview.config(image='')
    #     self.image_preview.image = None

    def load_image_preview(self, image_path):
        # Función para cargar la vista previa de la imagen
        if image_path:

            self.image = Image.open(image_path)
            self.image.thumbnail((200, 200))
            self.image_tk = ImageTk.PhotoImage(self.image)
            self.image_preview.config(image=self.image_tk)
            self.image_preview.image = self.image_tk

            # image = Image.open(image_path)
            # image = image.resize((150, 150), Image.LANCZOS)
            # photo = ImageTk.PhotoImage(image)
            # self.image_preview.config(image=photo)
            # self.image_preview.image = photo
        else:
            self.image_preview.config(image=None)

    def save_campaign(self, campaign_type):
        # Función para guardar una nueva campaña o actualizar una existente
        campaign_title = self.entry_name.get().strip()
        campaign_message = self.text_campaign.get("1.0", tk.END).strip()
        # campaign_image = self.file_path if self.file_path else ""
        image_path = ""
        absolute_image_path = ""

        if not campaign_title or not campaign_message:
            messagebox.showerror("Error", "Por favor completa todos los campos.")
            return
        
        # Guardar imagen si está seleccionada
        if self.image:
            # Directorio donde se guardan las imágenes
            images_dir = os.path.join(self.script_dir, "data/imagenes")
            os.makedirs(images_dir, exist_ok=True)
            # Obtener nombre de archivo de la imagen
            image_filename = os.path.basename(self.image.filename)
            image_path = os.path.join(images_dir, image_filename)

            # Copiar la imagen si no existe
            if not os.path.exists(image_path):
                shutil.copyfile(self.image.filename, image_path)
            # Convertir la ruta relativa en una ruta absoluta y normalizarla
            absolute_image_path = os.path.abspath(image_path).replace("\\", "/")

        

        campaign_data = {
            "title": campaign_title,
            "message": campaign_message,
            "image": absolute_image_path
        }

        campaigns_dir = os.path.join(self.script_dir, "data/campañas")
        # Crear el directorio si no existe
        os.makedirs(campaigns_dir, exist_ok=True)
        
        campaigns_file = os.path.join(self.script_dir, "data/campañas/"+campaign_type+".json")
        if os.path.exists(campaigns_file):
            with open(campaigns_file, "r") as f:
                campaigns_list = json.load(f)
        else:
            campaigns_list = []

        # Verificar si la campaña ya existe y actualizarla
        campaign_exists = False
        for idx, existing_campaign in enumerate(campaigns_list):
            if existing_campaign["title"] == campaign_title:
                campaigns_list[idx] = campaign_data
                campaign_exists = True
                break

        # Si no existe, añadir la nueva campaña
        if not campaign_exists:
            campaigns_list.append(campaign_data)

        # Guardar en el archivo JSON
        # with open(campaigns_file, "w") as f:
        #     json.dump(campaigns_list, f, indent=4)

        # Guardar en el archivo JSON
        with open(campaigns_file, "w", ) as f:
            json.dump(campaigns_list, f, indent=4)
        

        messagebox.showinfo("Campaña Guardada", "Campaña guardada exitosamente.")

        # Limpiar los campos después de guardar
        self.entry_name.delete(0, tk.END)
        self.text_campaign.delete(1.0, tk.END)
        self.image_preview.config(image=None)
        self.file_path = None
        self.image = None
        self.image_path = ""
        self.image_preview.config(image='')
        self.image_preview.image = None

        # Actualizar la tabla de campañas
        self.tree.delete(*self.tree.get_children())
        self.load_campaigns(campaign_type = campaign_type)

    def load_image(self):
        # Función para cargar una imagen desde el sistema
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if file_path:
            # self.image = Image.open(file_path)
            self.load_image_preview(file_path)

    def delete_campaign(self, campaign_type):
        # Obtener la campaña seleccionada en la tabla
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Por favor selecciona una campaña para eliminar.")
            return

        # Obtener el título de la campaña seleccionada
        campaign_title = self.tree.item(selected_item)["values"][0]
        campaigns_file = os.path.join(self.script_dir, "data/campañas/"+campaign_type+".json")
        if os.path.exists(campaigns_file):
            with open(campaigns_file, "r") as f:
                campaigns_list = json.load(f)
            
            # Eliminar la campaña del archivo JSON
            campaigns_list = [campaign for campaign in campaigns_list if campaign["title"] != campaign_title]

            # Guardar de nuevo en el archivo JSON
            with open(campaigns_file, "w") as f:
                json.dump(campaigns_list, f, indent=4)

            # Actualizar la tabla de campañas
            self.tree.delete(*self.tree.get_children())
            self.load_campaigns(campaign_type=campaign_type)
            # Limpiar los campos después de guardar
            self.entry_name.delete(0, tk.END)
            self.text_campaign.delete(1.0, tk.END)
            self.image_preview.config(image=None)
            self.file_path = None
            messagebox.showinfo("Campaña Eliminada", "Campaña eliminada exitosamente.")

    def run(self):
        self.mainloop()

if __name__ == "__main__":
    app = App()
    app.run()
