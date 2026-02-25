from flask import Flask, request, jsonify
from google import genai
import requests
import os

app = Flask(__name__)

# --- SECURE CONFIGURATION ---
# Ye values ab aap Vercel ki "Environment Variables" settings mein dalenge
WA_TOKEN = os.environ.get("WA_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "MERA_SECRET_TOKEN_123")

# Client initialize tabhi hoga jab API Key maujood ho
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

@app.route("/", methods=["GET"])
def health_check():
    return "Bot is running securely!"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Meta verification
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Wrong Token", 403

    if request.method == "POST":
        data = request.json
        try:
            # Check if it's a message from WhatsApp
            if "messages" in data["entry"][0]["changes"][0]["value"]:
                msg_value = data["entry"][0]["changes"][0]["value"]["messages"][0]
                msg_body = msg_value["text"]["body"]
                sender = msg_value["from"]
                
                # 1. Generate AI Response
                if client:
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=f"Aap ek desi dost hain. Roman Urdu mein chota jawab den: {msg_body}"
                    )
                    ai_answer = response.text
                else:
                    ai_answer = "Dost, API Key missing hai!"

                # 2. Send Message back via Graph API
                url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {WA_TOKEN}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "to": sender,
                    "type": "text",
                    "text": {"body": ai_answer}
                }
                requests.post(url, json=payload, headers=headers)
                
        except Exception as e:
            print(f"Error: {e}")
            
        return "OK", 200