# Victoria - Intelligent Voice Orchestrator

![Status](https://img.shields.io/badge/Status-Beta-blue)
![Architecture](https://img.shields.io/badge/Architecture-Hexagonal-green)
![Coverage](https://img.shields.io/badge/Coverage-72%25-yellow)

Victoria is a scalable, real-time voice agent orchestrator designed to manage complex conversational flows using LLMs, TTS, and STT services. It follows a strict **Hexagonal Architecture** to ensure maintenance and scalability.

## 📚 Documentation

- **Architecture**: [Deep Dive into Hexagonal Design](docs/architecture/ARCHITECTURE.md)
- **Setup**: [Development Guide](docs/development/SETUP.md)
- **Deployment**: [Production & Secrets](docs/deployment/SECRETS.md)
- **API**: Check `/docs` endpoint when running the server.

## 🚀 Key Features

- **Real-time Audio**: WebSocket streaming with VAD (Voice Activity Detection).
- **Multi-Provider Support**: 
  - LLM: Groq (Llama 3), OpenAI (GPT-4)
  - TTS: Azure, ElevenLabs
  - STT: Azure, Deepgram
  - Telephony: Twilio, Telnyx
- **Observability**: Built-in Prometheus metrics, Sentry error tracking, and structured JSON logging.
- **Resilience**: Circuit breakers and fallback mechanisms for AI services.

## 🛠 Tech Stack

- **Backend**: Python 3.10, FastAPI, SQLAlchemy (Async), Pydantic.
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS.
- **Infrastructure**: Docker, Nginx, SQLite/PostgreSQL.

## 🤝 Contributing

Please read [SETUP.md](docs/development/SETUP.md) for instructions on how to set up your development environment.
