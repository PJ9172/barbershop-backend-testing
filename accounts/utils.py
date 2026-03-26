import requests

FAST2SMS_API_KEY = "yJmo6SXJldT3sUR3jZd1s89xPi2F0L6yJAVP6EK14sKVdurlc8i1pCmRPYML"

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