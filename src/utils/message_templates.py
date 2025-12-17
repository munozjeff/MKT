"""
Plantillas de mensajes y generación de mensajes aleatorios.
"""
import random
import re
import numpy as np
from faker import Faker

fake = Faker()

# Plantillas por tema
SALUDOS = [
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

MENSAJES_BIENVENIDA = [
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

RECORDATORIOS = [
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

DETALLES_RECORDATORIO = [
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

DESPEDIDAS = [
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

PREGUNTAS = [
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

SUGERENCIAS = [
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


def generate_random_message():
    """
    Genera un mensaje aleatorio combinando diferentes plantillas.
    
    Returns:
        str: Mensaje aleatorio generado
    """
    name = fake.first_name()
    tema = fake.word()
    fecha = fake.date()
    seccion = fake.word()
    
    saludo = random.choice(SALUDOS).format(name=name)
    bienvenida = random.choice(MENSAJES_BIENVENIDA)
    pregunta = random.choice(PREGUNTAS).format(tema=tema, seccion=seccion)
    recordatorio = random.choice(RECORDATORIOS).format(tema=tema, fecha=fecha, seccion=seccion)
    detalle = random.choice(DETALLES_RECORDATORIO)
    sugerencia = random.choice(SUGERENCIAS).format(tema=tema, seccion=seccion)
    despedida = random.choice(DESPEDIDAS).format(name=name)
    
    return f"{saludo} {bienvenida} {pregunta} {recordatorio} {detalle} {sugerencia} {despedida}"


def replace_variables(text_template, variables, default_campaign=""):
    """
    Reemplaza variables en una plantilla de texto.
    
    Args:
        text_template (str): Plantilla con variables entre corchetes [variable]
        variables (dict): Diccionario con valores de las variables
        default_campaign (str): Campaña predeterminada si falta alguna variable
        
    Returns:
        str: Texto con variables reemplazadas o campaña predeterminada
    """
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
            return default_campaign

    return result_text
