import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(to_email, name):
    subject = "✂ Welcome to Barber Booking App ✂"
    body = f"""Hello {name},\n\nThanks for signing up! We're excited to have you at our barber shop.
        \n\nYou can now book appointments directly from the app.
        \n\nCheers,\nBarber App Team 💇‍♂️
    """
    
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg.set_content(body)
    
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email : {e}")


def send_profile_update_email(to_email, name):
    subject = "Profile Updated Successfully"

    body = f"""
        Hello {name},\n\nYour email has been successfully added to your profile.
        \n\nYou will now receive booking updates and important notifications on this email address.
        \n\nThank you,\nBarber Shop Team 💇‍♂️
        """
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg.set_content(body)
    
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email : {e}")