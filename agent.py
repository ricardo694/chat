from groq import Groq
import json
import unicodedata
import os


client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -------------------------------------------------------
# Función para normalizar mensajes (acentos, may/min)
# -------------------------------------------------------
def normalizar_texto(texto):
    if not isinstance(texto, str):
        return texto
    texto = texto.lower().strip()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


class Agente:
    def __init__(self, model="llama-3.1-8b-instant", max_history=10):
        self.model = model
        self.conversation_history = []
        self.max_history = max_history
        self.topics_proposed = []
        self.product_context = {}

        self.system_prompt = """
Eres un agente conversacional inteligente, natural y amigable.

Tu objetivo es ayudar al usuario a hablar sobre productos, vendedores, reseñas, 
calificaciones y tendencias de compra usando únicamente los datos que recibe en el contexto.

INSTRUCCIONES DE COMPORTAMIENTO:

1. Si recibes datos reales (productos, vendedores, métricas, reseñas):
   - Úsalos estrictamente.
   - No inventes información adicional.

2. Si recibes una descripción genérica del producto (“producto_descripcion”), 
   genera una explicación profesional con tono vendedor.

3. Si el contexto viene vacío o no contiene datos:
   - Puedes conversar libremente (saludos, preguntas generales, explicaciones).
   - Puedes dar descripciones generales de productos o conceptos.
   - Nunca inventes números, estadísticas o datos específicos de la base de datos.

4. Estilo:
   - Responde siempre en español.
   - Tono natural, cálido y conversacional.
   - Sé claro, útil y proactivo.

        """

    # ---------------------------------------------------
    # HISTORIAL
    # ---------------------------------------------------
    def add_to_history(self, role, content):
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def get_messages(self):
        return [{"role": "system", "content": self.system_prompt}] + self.conversation_history
    

    # ---------------------------------------------------
    # CONTEXTO DE PRODUCTO MEJORADO
    # ---------------------------------------------------
    def actualizar_contexto_producto(self, mensaje_usuario):
        msg = normalizar_texto(mensaje_usuario)

        # Detectar marca
        if "marca " in msg:
            palabra = msg.split("marca ")[1].strip().split(" ")[0]
            if palabra:
                self.product_context["marca"] = palabra

        # Color
        if "color " in msg:
            palabra = msg.split("color ")[1].strip().split(" ")[0]
            if palabra:
                self.product_context["color"] = palabra

        # Tamaño
        if "tamano " in msg:
            palabra = msg.split("tamano ")[1].strip().split(" ")[0]
            if palabra:
                self.product_context["tamaño"] = palabra

        if "tamaño " in msg:
            palabra = msg.split("tamaño ")[1].strip().split(" ")[0]
            if palabra:
                self.product_context["tamaño"] = palabra

        # Tipo
        if "tipo " in msg:
            palabra = msg.split("tipo ")[1].strip().split(" ")[0]
            if palabra:
                self.product_context["tipo"] = palabra
    # ---------------------------------------------------
    # CHAT PRINCIPAL
    # ---------------------------------------------------
    def chat(self, user_message, datos_bd=None):

        # Guardamos mensaje normalizado (mejora de intención)
        user_message_norm = normalizar_texto(user_message)

        # Actualizamos contexto
        self.actualizar_contexto_producto(user_message_norm)

        # -------------------------
        # REGLAS DE DATOS
        # -------------------------

        # Caso A → None = conversación libre
        if datos_bd is None:
            contexto_bd = ""

        # Caso B → datos vacíos
        elif isinstance(datos_bd, (dict, list)) and len(datos_bd) == 0:

        # El usuario pide descripción general → Permitido
            if any(p in user_message_norm for p in [
                "describ", "descripcion", "caracteristica", "caracteristicas",
                "info", "que es", "qué es", "detalles", "sobre"
            ]):
                datos_bd = None
                contexto_bd = ""

            # El usuario NO está pidiendo datos → conversación libre
            elif any(p in user_message_norm for p in [
                "hola", "buenas", "hey", "como estas", "qué puedes hacer",
                "ayuda", "ayudame", "puedes hablar", "quiero hablar"
            ]):
                datos_bd = None
                contexto_bd = ""

            # El usuario SÍ pide datos reales → no hay datos reales → responder
            else:
                return "No hay información disponible en este momento."

        # Caso C → Datos reales
        else:
            if isinstance(datos_bd, dict) and "producto_descripcion" in datos_bd:
                contexto_bd = (
                    "\nEl usuario quiere una descripción comercial del producto:\n"
                    f"- {datos_bd['producto_descripcion']}\n"
                    "Genera una descripción persuasiva, clara y profesional.\n"
                )
            else:
                contexto_bd = "\nDatos reales de la base de datos:\n" + json.dumps(datos_bd, indent=2) + "\n"

        # -------------------------
        # CONTEXTO DEL PRODUCTO
        # -------------------------
        contexto_producto = ""
        if self.product_context:
            contexto_producto = (
                "\nContexto acumulado del producto:\n"
                + json.dumps(self.product_context, indent=2)
            )
        contexto_dinamico = contexto_bd + contexto_producto

        self.add_to_history("user", user_message)

        # --------------------------
        # GENERAR MENSAJES
        # --------------------------
        messages = self.get_messages()
        messages.append({"role": "system", "content": contexto_dinamico})

        # -------------------------
        # LLAMADA A GROQ
        # -------------------------
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages = self.get_messages() + [{"role": "system", "content": contexto_dinamico}],
                temperature=0.6,
            )

            assistant_message = response.choices[0].message.content

            self.add_to_history("assistant", assistant_message)
            return assistant_message

        except Exception as e:
            return f"Error al comunicarse con GROQ: {str(e)}"

    # ---------------------------------------------------
    # OTROS MÉTODOS
    # ---------------------------------------------------
    def propose_topic(self):
        return "¿Sobre qué producto, vendedor o categoría quieres hablar hoy?"

    def get_conversation_summary(self):
        if not self.conversation_history:
            return "No existe conversación activa."
        total = len(self.conversation_history)
        users = sum(1 for m in self.conversation_history if m["role"] == "user")
        return f"Resumen:\n- Total mensajes: {total}\n- Mensajes usuario: {users}\n"

    def reset_conversation(self):
        self.conversation_history = []
        print("Reiniciando conversación...")

    def reset_contexto_producto(self):
        self.product_context = {}


# -------------------------------------------------------
# AGENTE GLOBAL PARA FASTAPI
# -------------------------------------------------------
agente_global = Agente(model="llama-3.1-8b-instant")

def run_agent(mensaje_usuario, datos_bd=None):
    return agente_global.chat(mensaje_usuario, datos_bd)
