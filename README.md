# NexBot: Intelligent 3D Educational Policy Assistant

NexBot is an interactive 3D web application designed to act as an intelligent assistant for educational policy. It combines a highly responsive 3D avatar frontend with a powerful Retrieval-Augmented Generation (RAG) backend to provide accurate, context-aware responses to user queries.

![Status](https://img.shields.io/badge/Status-Active-success)
![Frontend](https://img.shields.io/badge/Frontend-React%20%7C%20Three.js-blue)
![Backend](https://img.shields.io/badge/Backend-Flask%20%7C%20LangChain-green)

## 🚀 Features

- **Interactive 3D Avatar**: A fully animated 3D character (NexBot) built with React Three Fiber that responds to user interactions.
- **Natural Language Processing**: Powered by a Python Flask backend using LangChain and a local ChromaDB vector store for accurate policy retrieval.
- **Hybrid Modes**: Switch seamlessly between a text-only interface and the immersive 3D avatar experience.
- **RAG Architecture**: Uses intelligent document parsing and embedding retrieval to ground answers in specific educational policy data.
- **Voice Integration**: Supports audio feedback features for a more conversational experience.

## 🛠 Tech Stack

### Frontend (`3d-Frontend/`)

- **Core**: React, Vite
- **3D Graphics**: Three.js, React Three Fiber (`@react-three/fiber`), Drei (`@react-three/drei`)
- **UI/Styling**: Tailwind CSS
- **Controls**: Leva

### Backend (`ChatBot-Backend/`)

- **Server**: Flask (Python)
- **AI/ML**: LangChain, OpenAI/Google GenAI integrations
- **Vector DB**: ChromaDB (locally hosted sqlite3)
- **Data Processing**: Pandas, PyMuPDF, python-docx

## 📂 Project Structure

```bash
Chatbot-Edu/
├── 3d-Frontend/           # React + Vite Frontend application
│   ├── public/            # Static assets (3D models, animations)
│   ├── src/
│   │   ├── components/    # React components (Avatar, NexBot, UI)
│   │   ├── hooks/         # Custom hooks (e.g., useChat)
│   │   └── App.jsx        # Main application entry
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── ChatBot-Backend/       # Python Flask Backend
│   ├── app.py             # Main Flask application
│   ├── chroma_db/         # Local vector database storage
│   ├── audios/            # Audio file storage for responses
│   ├── utils/             # Helper scripts (retriever, loader)
│   ├── integrated_backend.py
│   └── requirements.txt
└── README.md
```

## ⚡ Getting Started

### Prerequisites

- Node.js (v16+)
- Python (v3.9+)
- npm or yarn

### 1. Backend Setup

Navigate to the backend directory and set up the Python environment.

```bash
cd ChatBot-Backend

# Create a virtual environment (optional but recommended)
python -m venv venv
# On Windows: venv\Scripts\activate
# On Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Make sure to configure your environment variables (API keys for OpenAI/Google) in a `.env` file within the `ChatBot-Backend` directory.

### 2. Frontend Setup

Navigate to the frontend directory and install dependencies.

```bash
cd 3d-Frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

### 3. Running the Application

1. **Start the Backend**: Run `python integrated_backend.py` (or `app.py` depending on your entry point) in the `ChatBot-Backend` terminal.
2. **Start the Frontend**: Run `npm run dev` in the `3d-Frontend` terminal.
3. Open the local URL provided by Vite (e.g., `http://localhost:5173`) to interact with NexBot.

## 🤝 Contribution

Feel free to fork the repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is open-source.
