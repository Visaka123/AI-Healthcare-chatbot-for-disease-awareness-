import os
import uuid
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from requests.auth import HTTPBasicAuth

# ------------------- LangChain -------------------
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_community.utilities import ArxivAPIWrapper
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# ------------------- Voice + Translation -------------------
from groq import Groq as GroqClient
from deep_translator import GoogleTranslator

# ------------------- ENV -------------------
load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# ------------------- APP -------------------
app = Flask(__name__)

# ------------------- GROQ WHISPER CLIENT -------------------
groq_client = GroqClient(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio(audio_path: str) -> tuple[str, str]:
    """Transcribe audio using Groq Whisper large-v3. Returns (text, language)."""
    with open(audio_path, "rb") as f:
        result = groq_client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f.read()),
            model="whisper-large-v3",
            response_format="verbose_json"
        )
    return result.text.strip(), getattr(result, "language", "en")

# ------------------- MEDICAL DATA -------------------
medical_urls = [
    "https://www.mayoclinic.org/diseases-conditions/diabetes/symptoms-causes/syc-20371444",
    "https://www.mayoclinic.org/diseases-conditions/hypertension/symptoms-causes/syc-20373410",
    "https://www.mayoclinic.org/diseases-conditions/asthma/symptoms-causes/syc-20369653"
]

all_docs = []
for url in medical_urls:
    loader = WebBaseLoader(url)
    docs = loader.load()
    all_docs.extend(docs)

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
documents = splitter.split_documents(all_docs)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectordb = FAISS.from_documents(documents, embeddings)
retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# ------------------- TOOLS -------------------
@tool
def search_medical_articles(query: str) -> str:
    """Search medical information from trusted documents."""
    docs = retriever.invoke(query)
    return "\n\n".join(doc.page_content for doc in docs)

arxiv_wrapper = ArxivAPIWrapper(top_k_results=3, doc_content_chars=500)

@tool
def search_medical_research(query: str) -> str:
    """Search medical research papers."""
    return arxiv_wrapper.run(query)

tools = [search_medical_articles, search_medical_research]

# ------------------- LLM -------------------
llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0
)

SYSTEM_PROMPT = """
You are a friendly medical assistant.
Give short, clear answers.
Do NOT give diagnosis.
Suggest possible causes.
Always end your response by recommending the type of doctor to visit (e.g. General Physician, Neurologist, Cardiologist, etc.) based on the symptoms.
"""

agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT
)


def get_agent_executor(query: str, lang: str = "en") -> str:
    """Entry point for chatbot and WhatsApp to query the agent."""
    if lang == "ta":
        full_query = f"{query}\n\n(Please respond entirely in Tamil language)"
    else:
        full_query = query
    result = agent.invoke({"messages": [HumanMessage(content=full_query)]})
    return result["messages"][-1].content

# ------------------- LANGUAGE -------------------
def detect_language(text):
    if text and any('\u0B80' <= ch <= '\u0BFF' for ch in text):
        return "ta"
    return "en"
print("🔥 WEBHOOK HIT")
# ------------------- WHATSAPP -------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    print("\n🔥 WEBHOOK HIT")

    response = MessagingResponse()
    msg = response.message()

    try:
        num_media = int(request.form.get("NumMedia", 0))
        incoming_msg = request.form.get("Body")
        whisper_lang = None

        print("NumMedia:", num_media)
        print("Body:", incoming_msg)
        print("MediaUrl0:", request.form.get("MediaUrl0"))



        # ================= VOICE HANDLING =================
        if num_media > 0:
            media_content_type = request.form.get("MediaContentType0", "")
            if "audio" not in media_content_type:
                msg.body("⚠️ Please send a voice message, not an image or file.")
                return str(response)

            media_url = request.form.get("MediaUrl0")
            print("📥 Downloading audio...")

            audio_data = requests.get(
                media_url,
                auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            ).content

            audio_path = f"audio_{uuid.uuid4().hex}.ogg"
            with open(audio_path, "wb") as f:
                f.write(audio_data)

            print("🎤 Transcribing...")
            try:
                incoming_msg, whisper_lang = transcribe_audio(audio_path)
            finally:
                os.remove(audio_path)

            print("🧠 Whisper Output:", incoming_msg)

            if not incoming_msg or len(incoming_msg) < 2:
                msg.body("⚠️ I couldn't understand your voice. Please speak clearly.")
                return str(response)

        # ================= TEXT EMPTY CHECK =================
        if not incoming_msg or len(incoming_msg.strip()) == 0:
            msg.body("⚠️ Please send a valid message.")
            return str(response)

        print("👤 Final User Message:", incoming_msg)

        # ================= LANGUAGE =================
        lang = whisper_lang if whisper_lang else detect_language(incoming_msg)
        print("🌍 Detected Language:", lang)

        if lang == "ta":
            translated_msg = GoogleTranslator(source='auto', target='en').translate(incoming_msg)
        else:
            translated_msg = incoming_msg

        print("🌐 Translated:", translated_msg)

        # ================= AI =================
        reply_text = get_agent_executor(translated_msg, lang)

        msg.body(reply_text)

    except Exception as e:
        print("❌ Error:", e)
        msg.body("⚠️ Error occurred. Try again.")

    return str(response)

FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")

def truncate_for_sms(text: str, limit: int = 1550) -> str:
    """Truncate reply to fit SMS character limit."""
    if len(text) <= limit:
        return text
    return text[:limit] + "...(reply truncated)"


def send_sms_india(phone: str, message: str):
    """Send SMS via Fast2SMS to Indian numbers."""
    requests.post(
        "https://www.fast2sms.com/dev/bulkV2",
        headers={"authorization": FAST2SMS_API_KEY},
        data={
            "route": "q",
            "message": message[:160],
            "language": "english",
            "flash": 0,
            "numbers": phone
        }
    )

# ------------------- SMS FORWARDER -------------------
@app.route("/sms-forward", methods=["POST"])
def sms_forward():
    try:
        data = request.get_json(force=True)
        print("📩 SMS Forwarder raw data:", data)

        # SMS Forwarder wraps content in 'key' field as a string
        import json as json_lib
        if "key" in data:
            raw = data["key"]
            # extract phone and message directly using string parsing
            try:
                # try parsing as json first
                inner = json_lib.loads(raw)
                phone = inner.get("in-number", "").strip()
                user_message = inner.get("msg", "").strip()
            except:
                # fallback: extract using split
                import re
                phone_match = re.search(r'in-number[":\s]+([+\d]+)', raw)
                msg_match = re.search(r'msg[":\s,]+"([^"]+)"', raw)
                phone = phone_match.group(1).strip() if phone_match else ""
                user_message = msg_match.group(1).strip() if msg_match else ""
        else:
            phone = (
                data.get("in-number") or
                data.get("Incoming Number") or
                data.get("phone") or
                data.get("from") or ""
            ).strip()
            user_message = (
                data.get("msg") or
                data.get("Message Body") or
                data.get("message") or
                data.get("text") or ""
            ).strip()

        print(f"📩 SMS from {phone}: {user_message}")

        if not phone or not user_message:
            return jsonify({"error": "phone and message required"}), 400

        lang = detect_language(user_message)
        query = GoogleTranslator(source='auto', target='en').translate(user_message) if lang == "ta" else user_message
        reply = get_agent_executor(query, lang)
        reply = truncate_for_sms(reply)

        # Send reply back via Twilio SMS
        from twilio.rest import Client
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        twilio_client.messages.create(
            body=reply,
            from_="+12602613204",
            to=phone if phone.startswith("+") else "+91" + phone
        )
        print(f"📲 Twilio SMS reply sent to {phone}")
        return jsonify({"status": "sent", "reply": reply})

    except Exception as e:
        print("❌ SMS Forward Error:", e)
        return jsonify({"error": "Something went wrong."}), 500

@app.route("/sms-india", methods=["POST"])
def sms_india():
    try:
        data = request.get_json()
        phone = (data or {}).get("phone", "").strip()
        user_message = (data or {}).get("message", "").strip()

        if not phone or not user_message:
            return jsonify({"error": "phone and message are required"}), 400

        lang = detect_language(user_message)
        query = GoogleTranslator(source='auto', target='en').translate(user_message) if lang == "ta" else user_message
        reply = get_agent_executor(query, lang)
        reply = truncate_for_sms(reply, limit=160)

        send_sms_india(phone, reply)
        print(f"📲 SMS sent to {phone}")
        return jsonify({"status": "sent", "reply": reply})

    except Exception as e:
        print("❌ SMS India Error:", e)
        return jsonify({"error": "Something went wrong."}), 500



@app.route("/sms", methods=["POST"])
def sms_reply():
    print("\n📱 SMS HIT")

    response = MessagingResponse()
    msg = response.message()

    try:
        incoming_msg = request.form.get("Body", "").strip()
        print("📩 SMS Body:", incoming_msg)

        if not incoming_msg:
            msg.body("Please send a valid message.")
            return str(response)

        lang = detect_language(incoming_msg)

        if lang == "ta":
            translated_msg = GoogleTranslator(source='auto', target='en').translate(incoming_msg)
        else:
            translated_msg = incoming_msg

        print("🌐 Translated:", translated_msg)

        reply_text = get_agent_executor(translated_msg, lang)
        reply_text = truncate_for_sms(reply_text)

        msg.body(reply_text)

    except Exception as e:
        print("❌ SMS Error:", e)
        msg.body("Error occurred. Please try again.")

    return str(response)


# ------------------- CHATBOT API -------------------
@app.route("/chat", methods=["POST"])
def chat():
    try:
        # ---- Voice upload from chatbot ----
        if "audio" in request.files:
            audio_file = request.files["audio"]
            audio_path = f"audio_{uuid.uuid4().hex}.ogg"
            audio_file.save(audio_path)
            try:
                user_message, audio_lang = transcribe_audio(audio_path)
            finally:
                os.remove(audio_path)

            if not user_message or len(user_message) < 2:
                return jsonify({"error": "Could not understand audio."}), 400

        # ---- Text message from chatbot ----
        else:
            data = request.get_json()
            user_message = (data or {}).get("message", "").strip()
            audio_lang = None
            if not user_message:
                return jsonify({"error": "No message provided."}), 400

        lang = audio_lang if audio_lang else detect_language(user_message)
        query = GoogleTranslator(source='auto', target='en').translate(user_message) if lang == "ta" else user_message

        reply = get_agent_executor(query, lang)

        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ Chat Error:", e)
        return jsonify({"error": "Something went wrong."}), 500


# ------------------- RUN -------------------
if __name__ == "__main__":
    app.run(port=5000, debug=False)
