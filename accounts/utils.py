import requests
from dotenv import load_dotenv
import os

load_dotenv()

FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")

def send_otp(mobile, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"

    payload = {
        "variables_values": otp,
        "route": "otp",
        "numbers": mobile,
    }

    headers = {
        "authorization": FAST2SMS_API_KEY,
        'Content-Type': "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    # print("RAW RESPONSE:", response.text)  # Debug print
    return response.json()