"""
Agente LangChain básico.
Ejemplo mínimo basado en la documentación oficial.
"""

from dotenv import load_dotenv
from langchain.agents import create_agent

# Cargar variables de entorno desde .env
load_dotenv()


def get_weather(city: str) -> str:
    """Obtiene el clima de una ciudad (función de ejemplo)."""
    return f"El clima en {city} está soleado y 25°C!"


# Crear el agente con un modelo, herramientas y prompt del sistema
agent = create_agent(
    model="openai:gpt-4o",
    tools=[get_weather],
    system_prompt="Eres un asistente útil que responde en español.",
)

# Ejecutar el agente con una consulta
if __name__ == "__main__":
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "¿Cuál es el clima en Madrid?"}]}
    )
    print(result["messages"][-1].content)

