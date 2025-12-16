from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import run_agent, agente_global
from intents import INTENCIONES, ejecutar_intencion
import unicodedata

app = FastAPI()


class ChatInput(BaseModel):
    mensaje: str
    datos_bd: dict | None = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Normalizar texto
# --------------------------
def normalizar(texto: str):
    texto = texto.strip()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

# --------------------------
# ENDPOINT PRINCIPAL
# --------------------------
@app.post("/chat")
async def chat_endpoint(data: ChatInput):
    try:
        mensaje_normalizado =  normalizar(data.mensaje)
        datos = data.datos_bd
        
        # ------------------------------------
        # COMANDOS DEL AGENTE
        # ------------------------------------

        if mensaje_normalizado == "salir":
            agente_global.reset_conversation()
            return {"respuesta": "Sesión finalizada. Si quieres hablar otra vez, escribe algo nuevo."}

        if mensaje_normalizado == "reiniciar":
            agente_global.reset_conversation()
            return {"respuesta": "Conversación reiniciada."}

        if mensaje_normalizado == "resumen":
            resumen = agente_global.get_conversation_summary()
            return {"respuesta": resumen}

        if mensaje_normalizado == "proponer":
            topic = agente_global.propose_topic()
            return {"respuesta": topic}

        # ------------------------------------
        # DETECCIÓN DE INTENCIÓN  SQL
        # ------------------------------------
        intencion_detectada = None

        for nombre_intencion, palabras_clave in INTENCIONES.items():
            if any(k in mensaje_normalizado for k in palabras_clave):
                intencion_detectada = nombre_intencion
                break

        if intencion_detectada:
            nueva_data = ejecutar_intencion(intencion_detectada, mensaje_normalizado)
            if nueva_data is not None:
                datos = nueva_data  

        # ------------------------------------
        # LLAMAR AL AGENTE
        # ------------------------------------
        respuesta = run_agent(data.mensaje, datos_bd=datos)
        return {"respuesta": respuesta}
    except Exception as e:
        return {"error": f"Error interno del servidor: {str(e)}"}