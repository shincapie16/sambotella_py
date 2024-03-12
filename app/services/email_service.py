import os
from dotenv import load_dotenv
from email.message import EmailMessage
import ssl
import smtplib

load_dotenv()

def enviar_correo(pedido,numero):
    email_sender = os.getenv("EMAIL")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_receiver = os.getenv("EMAIL_SENDER")
    productos = pedido.get("pedido").get("productos")
    cliente = pedido.get("pedido").get("cliente")
    metodo_pago = pedido.get("pedido").get("metodo_pago")
    direccion_entrega = pedido.get("pedido").get("direccion_entrega")
    subject = "Pedido del cliente: {}".format(cliente)

    body = (
        "Se ha realizado un nuevo pedido.\n\n"
        "Datos del cliente:\n"
        "Nombre: {}\n"
        "Número de contacto: {}\n\n"
        "Orden:\n{}\n\n"
        "Método de pago: {}\n"
        "Dirección de entrega: {}\n"
    ).format(
        cliente,
        numero,
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