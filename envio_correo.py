import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import os

smtp_server = 'smtp.gmail.com'  # Cambia esto al servidor SMTP que estés utilizando
smtp_port = 587  # Cambia esto al puerto adecuado
sender_email = 'anthony.mcg24@gmail.com'
sender_password = 'ltnv cxpw axyi himi'

# Detalles del correo electrónico
receiver_email = 'jeam.mendoza.melo@gmail.com'
subject = 'Reporte Reactiva por regiones'
body = 'Adjunto lo solicitado'

# Crear el objeto MIMEMultipart
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))


# Adjuntar archivo
file_paths = ['reportes_excel/top_5_inversion_AMAZONAS.xlsx',
              'reportes_excel/top_5_inversion_ANCASH.xlsx',
              'reportes_excel/top_5_inversion_APURIMAC.xlsx',
              'reportes_excel/top_5_inversion_AYACUCHO.xlsx']  # Cambia la ruta al archivo que quieras adjuntar
for file_path in file_paths:
    with open(file_path, 'rb') as file:
        attachment = MIMEApplication(file.read(), _subtype="csv")
        attachment.add_header('Content-Disposition', 'attachment', filename=file_path)
        msg.attach(attachment)
    
# Iniciar la conexión con el servidor SMTP
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()  # Iniciar el modo seguro
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, receiver_email, msg.as_string())

print('Correo enviado exitosamente')