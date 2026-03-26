# import redis
# import random
# import os

# REDIS_URL = os.getenv("REDIS_URL")

# if REDIS_URL:
#     redis_client = redis.Redis.from_url(REDIS_URL)
# else:
#     redis_client = redis.Redis(host='localhost', port=6379, db=0)


# def generate_otp():
#     return str(random.randint(100000, 999999))


# def save_otp(phone, otp):
#     redis_client.setex(f"otp:{phone}", 300, otp)


# def validate_otp(phone, otp):
#     stored_otp = redis_client.get(f"otp:{phone}")

#     if not stored_otp:
#         return False

#     if stored_otp.decode() == otp:
#         redis_client.delete(f"otp:{phone}")
#         return True

#     return False



import random
from datetime import datetime, timedelta

otp_store = {}

def generate_otp():
    return str(random.randint(100000, 999999))

def save_otp(phone, otp):
    expiry_time = datetime.now() + timedelta(minutes=5)
    otp_store[phone] = {"otp": otp, "expiry_time": expiry_time}

def validate_otp(phone, otp):
    record = otp_store.get(phone)

    if not record:
        return False

    if datetime.now() > record["expiry_time"]:
        return False

    if record["otp"] == otp:
        del otp_store[phone]
        return True

    return False