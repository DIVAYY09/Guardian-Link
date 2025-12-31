# Guardian-Link: Emergency Agent System

## **Quick Start**

To launch the full system (Backend + Frontend + Browser):

```bash
python run_app.py
```

---

## **Prerequisites**

1.  **Python 3.10+** (Backend)
2.  **Node.js 18+** (Frontend)
3.  **Visual C++ Build Tools** (for some Python packages)
4.  **API Keys** in `.env`:
    *   `GOOGLE_API_KEY` (Gemini Brain)
    *   `AZURE_VISION_KEY` & `AZURE_VISION_ENDPOINT`
    *   `AZURE_SPEECH_KEY` & `AZURE_SPEECH_REGION`

## **Manual Startup**

If you prefer to run services separately:

**1. Backend (Terminal 1)**
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**2. Frontend (Terminal 2)**
```bash
cd frontend
npm run dev
```

**3. Access**
Open [http://localhost:5173](http://localhost:5173) in your browser.

## **Troubleshooting**

*   **"System Error - Processing Halted"**: Ensure Backend is running and keys are valid.
*   **Audio not playing**: Check `backend/static` permissions or Azure Speech quota.
*   **Camera not showing**: Allow browser camera permissions.
