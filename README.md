# 🩺 AI-Driven Public Health Chatbot for Disease Awareness

An intelligent healthcare chatbot designed to provide **disease awareness, preventive guidance, and basic health support** through **WhatsApp, SMS, and web chat**.

Built using **Flask, LangChain, Groq LLM, and FAISS**, this system enables users—especially in rural and semi-urban areas—to access reliable healthcare information anytime.

---
## 📸 Demo & Screenshots

### 1️⃣ 📝 English Text Interaction

<a href="https://github.com/user-attachments/assets/e8a0e73b-06c8-4392-beea-93928b85920f">
  <img src="https://github.com/user-attachments/assets/e8a0e73b-06c8-4392-beea-93928b85920f" width="100%" />
</a>

---

### 2️⃣ 🌐 Multilingual Support (Tamil + English)

<a href="https://github.com/user-attachments/assets/d403e50d-5e01-4621-a3d5-74ad8e24c700">
  <img src="https://github.com/user-attachments/assets/d403e50d-5e01-4621-a3d5-74ad8e24c700" width="100%" />
</a>

---

### 3️⃣ 🎤 Voice Input (Speech-to-Text)

<a href="https://github.com/user-attachments/assets/b644e915-c722-42b9-8d89-4815ba145073">
  <img src="https://github.com/user-attachments/assets/b644e915-c722-42b9-8d89-4815ba145073" width="100%" />
</a>

---

### 4️⃣ 🗣️ Tamil Voice Interaction

<a href="https://github.com/user-attachments/assets/fc8cef92-0c90-4a88-b8c4-3a53b7227d6d">
  <img src="https://github.com/user-attachments/assets/fc8cef92-0c90-4a88-b8c4-3a53b7227d6d" width="100%" />
</a>

---

### 5️⃣ 📱 SMS-Based Communication

<a href="https://github.com/user-attachments/assets/cf94c06a-e927-472d-93f7-3c1fa9a03106">
  <img src="https://github.com/user-attachments/assets/cf94c06a-e927-472d-93f7-3c1fa9a03106" width="40%" />
</a>


## 🚀 Features

* 💬 **Chatbot Interface** (Web + WhatsApp + SMS)
* 🎤 **Voice Input Support** (Speech-to-Text using Groq Whisper)
* 🌐 **Multilingual Support** (English + Tamil)
* 🧠 **AI-Powered Responses** using Groq LLM (LLaMA-based)
* 📚 **Medical Knowledge Retrieval (RAG)** using FAISS + trusted sources
* 🧪 **Research Paper Search** via arXiv
* 📱 **SMS Integration** (Twilio + Fast2SMS)
* 🏥 **Doctor Recommendation System**
* ⚡ **Real-time Health Guidance**

---

## 🏗️ Tech Stack

| Category       | Technology                        |
| -------------- | --------------------------------- |
| Backend        | Flask                             |
| AI Framework   | LangChain                         |
| LLM            | Groq (LLaMA Models)               |
| Vector DB      | FAISS                             |
| Embeddings     | HuggingFace Transformers          |
| Voice AI       | Groq Whisper                      |
| Translation    | Google Translator                 |
| Messaging APIs | Twilio (WhatsApp & SMS), Fast2SMS |
| Data Sources   | Mayo Clinic, arXiv                |

---

## 📂 Project Structure

```
FederatedScholar/
│── app.py
│── agents.py
│── agent_handler.py
│── requirements.txt
│── .env
│── chat_memory/
│── medical_db/
```

---

## ⚙️ Setup Instructions

```bash
git clone https://github.com/Visaka123/AI-Healthcare-chatbot-for-disease-awareness-.git
cd FederatedScholar
pip install -r requirements.txt
python app.py
```

---

## 🔐 Environment Variables

```
GROQ_API_KEY=your_api_key
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
FAST2SMS_API_KEY=your_key
```

---

## 📡 API Endpoints

* `POST /chat` → Chatbot API
* `POST /sms` → SMS interaction
* `POST /whatsapp` → WhatsApp webhook
* `POST /sms-forward` → SMS forwarder

---

## ⚠️ Disclaimer

This chatbot **does NOT provide medical diagnosis**.
It is intended only for **awareness and educational purposes**.
Always consult a qualified healthcare professional.

---

## 🔐 Security Note

* Never expose API keys publicly
* Always use `.env` for secrets
* Add `.env` to `.gitignore`

---

## 📈 Future Scope

* Wearable device integration
* Appointment booking system
* Telemedicine features
* More regional languages
* Personalized health recommendations

---

## ⭐ Acknowledgements

* Mayo Clinic (medical data)
* arXiv (research papers)
* LangChain ecosystem
* Groq AI platform
* Twilio APIs

---
