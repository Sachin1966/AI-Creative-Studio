# AI Creative Studio v2.0 🎨✨

AI Creative Studio is a premium, multi-modal, feature-rich web application built with a FastAPI backend and a modern React (Vite) frontend. It brings together advanced AI modules for image generation, text/scriptwriting, client-side background removal, voice-to-image canvas, audio suite (TTS, background soundtrack mixing, Speech-to-Text), and computer vision.

---

## 📂 Project Structure

Below is the directory structure outlining the modular organization of the codebase:

```text
Context/
├── .env                          # Local environment variables (Hugging Face tokens, etc.)
├── start.bat                     # Single-click batch file to run both servers concurrently
├── app_streamlit_backup.py       # Legacy backup of the Streamlit version
├── backend/
│   ├── main.py                   # FastAPI application defining all AI routes and services
│   └── requirements.txt          # Python packages required for the backend
└── frontend/
    ├── package.json              # NPM dependencies & scripts (Vite, React, JSZip, etc.)
    ├── vite.config.js            # Vite configuration with proxy configurations (/api -> localhost:8000)
    ├── index.html                # Main HTML entry point
    └── src/
        ├── main.jsx              # React mounting file
        ├── App.jsx               # Navigation logic & shared states (Gallery, Prompt)
        ├── api.js                # Frontend API wrapper mapping FastAPI endpoints
        ├── index.css             # Unified styling system (glassmorphism, dark mode, animations)
        └── components/
            ├── Sidebar.jsx           # Premium sidebar navigation with status tags
            ├── ImageGenerator.jsx     # Main dashboard for FLUX.1 image generation
            ├── CreativeWriter.jsx     # Narrative generator & scriptwriting assistant
            ├── VoiceCanvas.jsx        # Web Speech API voice-to-image canvas
            ├── BackgroundRemover.jsx  # Client-side WASM background remover
            ├── AudioSuite.jsx         # Speech synthesis & transcription panel
            ├── VisionAI.jsx           # BLIP Image Captioner & prompt extractor
            ├── PromptLibrary.jsx      # Curated templates catalog
            └── Gallery.jsx            # LocalStorage-backed client gallery
```

---

## ⚡ Tech Stack & Architecture

### Backend: FastAPI
- **FastAPI**: Serving high-performance, asynchronous REST endpoints. Includes CORS middleware configured for development mapping (`http://localhost:5173`).
- **Pydantic**: Strongly-typed request validation (`ImageRequest`, `TTSRequest`, `TextRequest`).
- **Gradio Client**: Connects securely to the Hugging Face `hysts/image-captioning-with-blip` Space for keyless image captioning.
- **Speech Recognition**: Leverages Python's `speech_recognition` module for audio transcribing.
- **API Services**: Pollinations AI (Text, Image & Audio pipelines), Hugging Face (FLUX.1-schnell via API Inference).

### Frontend: React + Vite + Vanilla CSS
- **React**: Single Page Application (SPA) driven by state hooks for tabs, shared prompts, and reactive views.
- **Vite**: Provides lightning-fast HMR and handles local development proxying to prevent CORS conflicts:
  ```js
  // Proxy configuration maps client-side '/api' calls to backend:
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
  ```
- **Local Browser Modules**:
  - `@imgly/background-removal`: Runs subject segmentation locally in the browser using WASM models (no API key needed, zero server overhead).
  - **Web Speech API**: Uses standard browser speech recognition engines for hands-free live drawing.
- **Assets Persistence**: Saves user gallery state directly in `localStorage` as base64 data URIs, letting files persist across browser reloads.

---

## 🛠️ Detailed Module Walkthrough

### 1. 🎨 Image Generator (`ImageGenerator.jsx`)
Generate illustrations, conceptual art, and graphics with options tailored for advanced prompt engineering:
- **Multi-Engine Pipeline**: Toggle between **Pollinations Flux** (Fast, free, no auth) and **Hugging Face FLUX.1-schnell** (Inference API).
- **Prompt Enhancer**: Automatically expands short descriptions into descriptive prompts using a specialized LLM system prompt.
- **Configuration Controls**: Aspect ratios (`1:1`, `16:9`, `9:16`, `4:3`, `3:4`), style presets (Photorealistic, Anime, Cyberpunk, 3D Render), custom seeds, and batch sizing up to 4 images at once.

### 2. ✍️ AI Creative Scriptwriter (`CreativeWriter.jsx`)
Generate high-fidelity stories, scripts, or character concepts on the fly:
- Uses the **Pollinations Text service** powered by open LLMs.
- Select target **Genre** (Sci-Fi, Fantasy, Noir, Comedy, Thriller, Drama, Adventure) and **Tone** (Epic, Dramatic, Mysterious, Cyberpunk, Whimsical, Dark, Futuristic).
- Includes dynamic word count sizing (50 to 400 words) and a **one-click transition** to instantly load the script as an image prompt.

### 3. 🎙️ Live Voice-to-Image Canvas (`VoiceCanvas.jsx`)
Dictate art concepts verbally and watch the canvas materialize them:
- Harnesses the **Web Speech API** for real-time transcription directly in Chrome/Edge.
- Active visual wave animation displaying recording state.
- Combines style filters (Anime, Photorealistic, Cyberpunk, 3D Render) with the verbal description before requesting client-side generation.
- Features direct downloads and one-click saving.

### 4. ✂️ Client-Side Background Remover (`BackgroundRemover.jsx`)
Extract foreground subjects and create transparent `.png` assets:
- Powered by `@imgly/background-removal`.
- Process runs **locally in the browser** using WebAssembly, showing a detailed step-by-step progress percentage indicator.
- Support for uploading local files or picking assets directly from the **Studio Gallery** for quick editing.

### 5. 🔊 Audio Suite (`AudioSuite.jsx`)
A powerful audio utility split into two major tracks:
- **Speech Synthesis (TTS) & Real-Time Mixer**:
  - Convert text to voice via **Google Translate TTS** (multilingual translations to Tamil, Hindi, Spanish, French, Japanese, Korean) or **Pollinations AI Voices** (alloy, echo, onyx, etc.).
  - Mix generated speech with synth backgrounds (**Calm Zen Pad**, **Deep Tech Pulse**, or **Cosmic Drone**).
  - Web Audio API canvas visualizer displaying real-time frequencies during playback.
- **Speech-to-Text Transcription**:
  - Drag and drop `.wav` audio files.
  - Backend transcribes speech back to raw text with custom transcription export (`.txt`).

### 6. 🖼️ Vision AI (`VisionAI.jsx`)
Reverse-engineer prompts from existing images:
- Uses BLIP (Bootstrapping Language Image Pre-training) models.
- Upload an image to analyze its contents and generate a highly detailed prompt description.
- Automatically maps the description back to the **Image Generator** workspace with a single click.

### 7. 📚 Prompt Library (`PromptLibrary.jsx`)
A curated database of 48+ highly optimized, categorized prompts to inspire creative generations:
- Categories include: *Architecture & Cities*, *Nature & Landscapes*, *Characters & Portraits*, *Fantasy & Mythology*, *Sci-Fi & Futurism*, and *Art Styles*.

### 8. 🗂️ My Gallery (`Gallery.jsx`)
- Aggregates all images generated via the Image Generator, Background Remover, and Voice Canvas.
- Includes dynamic counts in the sidebar.
- Export options: Save single images, export your entire collection as a **ZIP file** (via `jszip` and `file-saver`), or clear the local database.

---

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.8+**
- **Node.js 18+**

### Step 1: Clone and Set Up Environment Variables
Create a file named `.env` in the root project folder:
```env
HF_TOKEN=your_hugging_face_token_here
LUMA_API_KEY=your_luma_api_key_here
```
> **Note**: An active `HF_TOKEN` is required if you want to use the Hugging Face FLUX provider. Pollinations endpoints work out of the box without keys.

### Step 2: Running with the Startup Script
The project includes a single-command startup file:
- Simply double-click **`start.bat`** on Windows.
- It will automatically launch the backend server (`uvicorn` on port `8000`) and the frontend compiler (`vite` on port `5173`).

---

### Step 3: Manual Startup (Alternative)

#### A. Backend Setup
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the FastAPI development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
4. Access interactive Swagger API Docs: `http://localhost:8000/docs`

#### B. Frontend Setup
1. Navigate to the frontend folder:
   ```bash
   cd ../frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Launch the development server:
   ```bash
   npm run dev
   ```
4. Open the studio application at: `http://localhost:5173`

---

## 🎨 Styling Design System

All visual layouts are controlled through a centralized design system located in `frontend/src/index.css`:
- **Glassmorphism**: Backdrop blur filters combined with semi-transparent card borders.
- **Harmonious Palette**: Styled using CSS variables (`--bg-primary`, `--bg-card`, `--accent`, `--border-color`) to deliver a modern, premium dark aesthetic.
- **Micro-Animations**: Transitions on button hover, loading skeletons, slide-in sidebar elements, and glowing transcription states.
