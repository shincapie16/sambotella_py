import openai
from dotenv import find_dotenv, load_dotenv

load_dotenv()

client = openai.OpenAI()

entrenador = client.beta.assistants.retrieve("asst_iGVxSYZ4B5ys3veg0ePkUioI")

thread = client.beta.threads.create(
    messages={
        "role":"user",
        "content": ""
    }
)
thread_id = thread.id

print(entrenador)