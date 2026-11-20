import os
import time
import base64
from email.message import EmailMessage
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=60000),  # 60 second se zyada intezar nahi
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
]

SHEET_ID = "14tx-UkT7YManDz8KcbGLrPtYfjgzUbyAOfEBryFLzZs"


def get_credentials():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return creds


def score_lead(message):
    prompt = f"""You are a lead qualification assistant for a freelancer who offers
AI automation services (invoice data extraction, Gmail AI auto-reply, AI chatbots).

Classify this lead message into exactly ONE category:
- Hot: clear need, mentions quantity, budget, price or deadline, ready to buy
- Warm: interested, asks about services, but gives no specific details
- Cold: vague, unrelated to our services, or very low intent
- Spam: advertising, scams, suspicious links, promotions

Message: {message}

Reply with only one word: Hot, Warm, Cold, or Spam."""

    models = ["gemini-3.5-flash-lite", "gemini-3.6-flash"]  # pehla busy ho to doosra

    for attempt in range(1, 4):  # 3 round
        for model in models:
            try:
                response = client.models.generate_content(
                    model=model, contents=prompt
                )
                answer = (response.text or "").strip()
                if answer in ["Hot", "Warm", "Cold", "Spam"]:
                    return answer
                return "Unknown"
            except Exception as e:
                print(f"   {model} failed (round {attempt}): {str(e)[:60]}")
        if attempt < 3:
            time.sleep(15)

    return "Unknown"

def generate_reply(name, message, score):
    prompt = f"""You are a friendly, professional assistant for Sattar Awan,
a freelancer who offers AI automation services:
- AI invoice data extraction (PDF invoices to Excel)
- Gmail AI auto-reply agents
- AI chatbots for websites and libraries

A lead named {name} sent this message (lead type: {score}):
"{message}"

Write a short, polite email reply (4-6 sentences):
- Thank them by name
- Answer their question as well as possible
- If they ask about price or timeline, say it depends on the exact scope and
  invite them to share a few details or a sample
- End by inviting them to reply or book a short call
- Sign off as: Sattar Awan

Do not invent prices, discounts or guarantees. Write only the email body."""

    models = ["gemini-3.5-flash-lite", "gemini-3.6-flash"]

    for attempt in range(1, 4):
        for model in models:
            try:
                response = client.models.generate_content(
                    model=model, contents=prompt
                )
                reply = (response.text or "").strip()
                if reply:
                    return reply
            except Exception as e:
                print(f"   {model} failed (round {attempt}): {str(e)[:60]}")
        if attempt < 3:
            time.sleep(15)

    return ""

def send_email(gmail, to, subject, body):
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    try:
        gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True
    except Exception as e:
        print("   send failed:", str(e)[:80])
        return False
creds = get_credentials()
sheets = build("sheets", "v4", credentials=creds)
gmail = build("gmail", "v1", credentials=creds)

result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID, range="Sheet1!A2:F"
).execute()
rows = result.get("values", [])

for i, row in enumerate(rows, start=2):
    name = row[0]
    message = row[2] if len(row) > 2 else ""
    reply = row[3] if len(row) > 3 else ""
    score = row[4] if len(row) > 4 else ""

    # 1) Score: sirf tab banao jab pehle se na ho
    if not score.strip():
        score = score_lead(message)
        sheets.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"Sheet1!E{i}",
            valueInputOption="RAW",
            body={"values": [[score]]},
        ).execute()
        print(name, "->", score)
    else:
        print(name, "-> already scored:", score)

    # 2) Reply: sirf Hot/Warm ko, aur sirf tab jab pehle se na ho
    if score in ["Hot", "Warm"] and not reply.strip():
        reply = generate_reply(name, message, score)
        if reply:
            sheets.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"Sheet1!D{i}",
                valueInputOption="RAW",
                body={"values": [[reply]]},
            ).execute()
            print("   reply saved")
            
                # 3) Email: sirf Hot/Warm, reply tayyar ho, aur pehle na bheji ho
    email = row[1] if len(row) > 1 else ""
    status = row[5] if len(row) > 5 else ""

    if score in ["Hot", "Warm"] and reply.strip() and not status.strip():
        print("\n--- Email to", name, "(" + email + ") ---")
        print(reply)
        choice = input("Send this email? (y/n): ").strip().lower()

        if choice == "y":
            ok = send_email(gmail, email, f"Thanks for your inquiry, {name}", reply)
            if ok:
                sheets.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"Sheet1!F{i}",
                    valueInputOption="RAW",
                    body={"values": [["Sent"]]},
                ).execute()
                print("   email sent ✅")
        else:
            sheets.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"Sheet1!F{i}",
                valueInputOption="RAW",
                body={"values": [["Skipped"]]},
            ).execute()
            print("   skipped")