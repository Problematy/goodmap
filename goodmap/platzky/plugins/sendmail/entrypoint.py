import smtplib
from functools import partial


def send_mail(sender_email, password, smtp_server, port, receiver_email, subject, message):
    full_message = f'From: {sender_email}\nTo: {receiver_email}\nSubject: {subject}\n\n{message}'

    server = smtplib.SMTP_SSL(smtp_server, port)
    server.ehlo()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, full_message)
    server.close()


def process(app):
    smtp_setup = app.config["SMTP"]
    app.sendmail = partial(send_mail,
                           smtp_setup["ADDRESS"],
                           smtp_setup["PASSWORD"],
                           smtp_setup["SERVER"],
                           smtp_setup["PORT"])
    return app
