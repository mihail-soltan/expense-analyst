import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

def send_monthly_email(summary_text, email_recipient, files_to_attach):
    # --- CONFIG ---
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_RECIPIENT = email_recipient
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = os.getenv('SMTP_PORT')
    # ---------------------

    msg = MIMEMultipart()
    msg['Subject'] = f"Monthly Expense Summary - {datetime.now().strftime('%B %Y')}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECIPIENT

    # attach body Text
    msg.attach(MIMEText(summary_text, 'html'))

    # Attach Images
    for filepath in files_to_attach:
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                img_data = f.read()
                image = MIMEImage(img_data, name=os.path.basename(filepath))
                msg.attach(image)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")