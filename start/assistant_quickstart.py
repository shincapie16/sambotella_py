from openai import OpenAI
import shelve
from dotenv import load_dotenv
import os
import time
import json

from email.message import EmailMessage
import ssl
import smtplib

load_dotenv()

def enviar_correo(pedido,numero):
    email_sender = os.getenv("EMAIL")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_receiver = os.getenv("EMAIL_SENDER")
    subject = "Pedido del numero: {}".format(numero)
    
    productos = pedido.get("pedido").get("productos")
    cliente = pedido.get("pedido").get("cliente")
    metodo_pago = pedido.get("pedido").get("metodo_pago")
    direccion_entrega = pedido.get("pedido").get("direccion_entrega")

    body = (
        "Pedido realizado por: {}\n"
        "Productos:\n"
        "{}"
        "Método de pago: {}\n"
        "Dirección de entrega: {}\n"
    ).format(
        cliente,
        ''.join([f"- {producto['nombre']}: ${producto['valor']}\n" for producto in productos]),
        metodo_pago,
        direccion_entrega
    )

    em = EmailMessage()
    em["From"] = email_sender
    em["To"] = email_receiver
    em["Subject"] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, email_receiver, em.as_string())
        return True
    except Exception as e:
        print(f"No se pudo enviar el correo: {str(e)}")
        return False
    
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
client = OpenAI(api_key=OPENAI_API_KEY)

OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

client = OpenAI(api_key=OPEN_AI_API_KEY)


# --------------------------------------------------------------
# Thread management
# --------------------------------------------------------------
def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id


# --------------------------------------------------------------
# Generate response
# --------------------------------------------------------------
def generate_response(message_body, wa_id, name):
    # Check if there is already a thread_id for the wa_id
    thread_id = check_if_thread_exists(wa_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        print(f"Creating new thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        print(f"Retrieving existing thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    # Run the assistant and get the new message
    new_message = run_assistant(thread,wa_id)
    print(f"To {name}:", new_message)
    return new_message


# --------------------------------------------------------------
# Run assistant
# --------------------------------------------------------------
def run_assistant(thread,wa_id):
    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    # Wait for completion
    while run.status != "completed":
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run.status == "requires_action":
            tools_to_call = run.required_action.submit_tool_outputs.tool_calls
            if (tools_to_call[0].function.name == 'enviar_correo'):
                enviado = enviar_correo(json.loads(tools_to_call[0].function.arguments),wa_id)
            tools_outputs_array = [({"tool_call_id": tools_to_call[0].id, "output": True})]

            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tools_outputs_array
            )

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    print(f"Generated message: {new_message}")
    return new_message


# --------------------------------------------------------------
# Test assistant
# --------------------------------------------------------------

new_message = generate_response("Cuales han sido mis pedidos?", "3323115", "Carlos")

# new_message = generate_response("What's the pin for the lockbox?", "456", "Sarah")

# new_message = generate_response("What was my previous question?", "123", "John")

# new_message = generate_response("What was my previous question?", "456", "Sarah")