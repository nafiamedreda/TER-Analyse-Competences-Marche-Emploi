import os
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

print("CLIENT_ID chargé :", client_id is not None)
print("CLIENT_SECRET chargé :", client_secret is not None)