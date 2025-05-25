import os
import json
import io
import csv
import logging
from fastapi import FastAPI, WebSocket, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
from dotenv import load_dotenv
import openai
from PyPDF2 import PdfReader
import unicodedata
from pydantic import BaseModel
from fuzzywuzzy import fuzz
import time
import uuid

from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import JSONResponse, FileResponse
import io
import json
import random
import logging
from PyPDF2 import PdfReader
import openai
import os
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware



# 🔐 Environment laden
load_dotenv()

# 🌍 FastAPI Setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# 🟢 OpenAI Client
client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 📌 HeyGen API Key
HEYGEN_API_KEY = "" #Enter HeyGen Key Here
AVATAR_ID = os.getenv("AVATAR_ID")
VOICE_ID = os.getenv("VOICE_ID")

# 📝 Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# 💾 In-memory message history
history = {}

# -----------------------------------------------
# 🚀 Flashcards Endpoints
# -----------------------------------------------
@app.get("/flashcards")
async def flashcard_page():
    return FileResponse("static/flashcards.html")

@app.post("/generate_flashcards")
async def generate_flashcards(file: UploadFile, num_flashcards: int = Form(...), depth: str = Form(...)):
    try:
        contents = await file.read()
        reader = PdfReader(io.BytesIO(contents))
        text = "\n".join([page.extract_text() or "" for page in reader.pages])

        if not text.strip():
            return JSONResponse({"error": "❌ PDF enthält keinen extrahierbaren Text."}, status_code=400)

        prompt = f"""
Du bist ein Lerncoach. Erstelle {num_flashcards} Lernkarten im Stil "Frage - Antwort" mit dem Schwierigkeitsgrad: {depth}.
Nutze den folgenden Text:
{text[:3000]}
        """

        completion = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        flashcards = completion.choices[0].message.content.strip()
        return JSONResponse({"flashcards": flashcards})

    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der Flashcards: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

def remove_umlaute(text):
    replacements = {
        "ä": "ae", "ö": "oe", "ü": "ue",
        "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
        "ß": "ss"
    }
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    return text

@app.post("/download_flashcards_csv")
async def download_csv(flashcards: str = Form(...)):
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Frage", "Antwort"])  # ✅ CSV Header

        current_question = None

        for line in flashcards.strip().splitlines():
            line = line.strip()
            if line.lower().startswith("frage"):
                current_question = line
            elif line.lower().startswith("antwort") and current_question:
                answer = line
                # 🟢 Entferne "Frage:" / "Antwort:" aus den Strings
                question_clean = current_question.replace("Frage:", "").strip()
                answer_clean = answer.replace("Antwort:", "").strip()
                # 🟢 Umlaute ersetzen:
                question_clean = remove_umlaute(question_clean)
                answer_clean = remove_umlaute(answer_clean)
                writer.writerow([question_clean, answer_clean])
                current_question = None  # Setze zurück für die nächste Runde

        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={
            "Content-Disposition": "attachment; filename=flashcards.csv"
        })
    except Exception as e:
        logger.error(f"❌ CSV-Export fehlgeschlagen: {e}")
        return JSONResponse({"error": f"CSV-Export fehlgeschlagen: {e}"}, status_code=500)

# -----------------------------------------------
# 🤖 Avatar Streaming + Chat Endpoints
# -----------------------------------------------
@app.get("/")
async def get():
    return FileResponse("static/avatar_player.html")

@app.websocket("/ws/avatar")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("✅ WebSocket-Verbindung geöffnet")

    session = aiohttp.ClientSession()
    session_token, session_id = None, None
    client_id = id(websocket)
    history[client_id] = [{
    "role": "system",
    "content": (
        "Du bist ein virtueller Hochschuldozent für Wirtschaftsinformatik. "
        "Deine Art ist freundlich, motivierend und geduldig. "
        "Du erklärst Fachinhalte einfach, anschaulich und studierendengerecht – auch komplexe Themen. "
        "Verwende kurze, verständliche Sätze und gib, wenn möglich, praxisnahe Beispiele. "
        "Gib motivierendes Feedback, fördere aktives Mitdenken und rege zur Reflexion an. "
        "Sprich in klarer, natürlicher Sprache und reagiere direkt auf Fragen oder Eingaben. "
        "Wenn du etwas nicht verstehst, sag höflich: 'Das habe ich akustisch nicht ganz verstanden – magst du es anders formulieren?' "
        "Du bist ein digitaler Avatar und hast keinen Zugriff auf E-Mails oder externe Systeme."
    )
}]


    try:
        # 🎫 Token erstellen
        async with session.post(
            "https://api.heygen.com/v1/streaming.create_token",
            headers={"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"}
        ) as token_resp:
            token_data = await token_resp.json()
            if "data" not in token_data:
                raise Exception(f"Token creation failed: {token_data}")
            session_token = token_data["data"]["token"]
            logger.info("✅ Token erfolgreich erstellt")

        # 🎬 Session starten
        payload = {"avatar_id": AVATAR_ID, "voice": {"voice_id": VOICE_ID}, "version": "v2"}
        async with session.post(
            "https://api.heygen.com/v1/streaming.new",
            headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"},
            json=payload
        ) as session_resp:
            session_data = await session_resp.json()
            if "data" not in session_data:
                raise Exception(f"Session creation failed: {session_data}")
            session_info = session_data["data"]
            session_id = session_info["session_id"]
            livekit_url = session_info["url"]
            token = session_info["access_token"]
            logger.info(f"✅ Session ID: {session_id}")

        # ▶️ Session aktivieren
        async with session.post(
            "https://api.heygen.com/v1/streaming.start",
            headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"},
            json={"session_id": session_id}
        ) as start_resp:
            start_data = await start_resp.json()
            if "data" not in start_data and start_resp.status != 200:
                raise Exception(f"Failed to start session: {start_data}")
            logger.info("✅ Streaming gestartet – Avatar sollte jetzt sichtbar sein!")

        await websocket.send_json({
            "type": "config",
            "livekit_url": livekit_url,
            "token": token,
            "session_id": session_id
        })

        # 💬 Nachrichtenloop (GPT <-> Avatar)
        while True:
            try:
                message_data = await websocket.receive_text()
                parsed_message = json.loads(message_data)

                # 🆕 NEU: Nur an Avatar senden, falls Typ "avatar"
                if parsed_message.get("type") == "avatar":
                    avatar_text = parsed_message["data"]
                    logger.info(f"📢 Nur an Avatar senden: {avatar_text}")
                    await session.post(
                        "https://api.heygen.com/v1/streaming.task",
                        headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"},
                        json={"session_id": session_id, "text": avatar_text, "task_type": "talk"}
                    )
                    continue  # 🔁 zurück zum nächsten receive


                
                msg_type = parsed_message.get("type")
                message_content = parsed_message.get("data", "")

                if msg_type == "gpt":
                    logger.info(f"👤 User (an GPT): {message_content}")

                    client_history = history[client_id]
                    client_history.append({"role": "user", "content": message_content})

                    gpt_response = await client.chat.completions.create(
                        model="gpt-4-1106-preview",
                        messages=client_history
                    )
                    assistant_reply = gpt_response.choices[0].message.content
                    logger.info(f"🤖 GPT Antwort: {assistant_reply}")

                    client_history.append({"role": "assistant", "content": assistant_reply})

                    # 🗣️ GPT-Antwort an Avatar
                    async with session.post(
                        "https://api.heygen.com/v1/streaming.task",
                        headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"},
                        json={"session_id": session_id, "text": assistant_reply, "task_type": "talk"}
                    ) as speak_resp:
                        speak_data = await speak_resp.json()
                        if "data" not in speak_data and speak_resp.status != 200:
                            logger.warning(f"Problem beim Senden an Avatar: {speak_data}")

                    await websocket.send_json({
                        "type": "gpt",
                        "message": assistant_reply,
                        "keywords": []  # Glossar bewusst deaktiviert
                    })

                elif msg_type == "avatar":
                    logger.info(f"🎤 Direkter Avatar-Befehl: {message_content}")
                    await session.post(
                        "https://api.heygen.com/v1/streaming.task",
                        headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"},
                        json={"session_id": session_id, "text": message_content, "task_type": "talk"}
                )
                continue  # ✅ Damit GPT-Teil NICHT auch noch ausgeführt wird


            except Exception as loop_error:
                logger.error(f"⚠️ Fehler im Nachrichtenloop: {loop_error}")
                break

    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass

    finally:
        if session_token and session_id:
            try:
                await session.post(
                    "https://api.heygen.com/v1/streaming.stop",
                    headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"},
                    json={"session_id": session_id}
                )
                logger.info("🛑 Session erfolgreich gestoppt.")
            except Exception as stop_error:
                logger.warning(f"Fehler beim Session-Stopp: {stop_error}")
        await session.close()
        await websocket.close()
        history.pop(client_id, None)

@app.websocket("/ws/kprim_avatar")
async def websocket_kprim_avatar(websocket: WebSocket):
    await websocket.accept()
    logger.info("✅ WebSocket-Verbindung für KPRIM Avatar geöffnet")

    session = aiohttp.ClientSession()
    session_token, session_id = None, None

    try:
        # 🔐 Token erstellen
        async with session.post(
            "https://api.heygen.com/v1/streaming.create_token",
            headers={"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"}
        ) as token_resp:
            token_data = await token_resp.json()
            session_token = token_data["data"]["token"]

        # 🎬 Neue Avatar-Session starten
        async with session.post(
            "https://api.heygen.com/v1/streaming.new",
            headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"},
            json={"avatar_id": AVATAR_ID, "voice": {"voice_id": VOICE_ID}, "version": "v2"}
        ) as session_resp:
            session_data = await session_resp.json()
            session_id = session_data["data"]["session_id"]
            livekit_url = session_data["data"]["url"]
            token = session_data["data"]["access_token"]

        # ▶️ Avatar-Session aktivieren
        await session.post(
            "https://api.heygen.com/v1/streaming.start",
            headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"},
            json={"session_id": session_id}
        )

        # 🟢 Konfigurationsdaten an Client schicken
        await websocket.send_json({
            "type": "config",
            "livekit_url": livekit_url,
            "token": token,
            "session_id": session_id
        })

        # 🎤 Feedback-Schleife
        while True:
            message_data = await websocket.receive_text()
            parsed_message = json.loads(message_data)
            feedback_text = parsed_message.get("data", "")

            logger.info(f"👤 Feedback erhalten: {feedback_text}")

            # 1. ✅ Nachricht ins Frontend zurücksenden (sichtbar für User)
            await websocket.send_json({
                "type": "gpt",
                "message": feedback_text
            })

            # 2. 🔊 Avatar soll sprechen
            await session.post(
                "https://api.heygen.com/v1/streaming.task",
                headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"},
                json={"session_id": session_id, "text": feedback_text, "task_type": "talk"}
            )

    except Exception as e:
        logger.error(f"❌ Fehler im KPRIM Avatar WebSocket: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})

    finally:
        # 🛑 Session beenden
        if session_token and session_id:
            await session.post(
                "https://api.heygen.com/v1/streaming.stop",
                headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"},
                json={"session_id": session_id}
            )
        await session.close()
        await websocket.close()




# -----------------------------------------------
# 🚀 KPRIM Quiz (Prüfungsmodus) Endpoint
# -----------------------------------------------
@app.get("/kprim")
async def kprim_page():
    return FileResponse("static/kprim.html")

@app.post("/generate_kprim")
async def generate_kprim(file: UploadFile, num_questions: int = Form(...)):
    try:
        contents = await file.read()
        reader = PdfReader(io.BytesIO(contents))
        text = "\n".join([page.extract_text() or "" for page in reader.pages])

        if not text.strip():
            return JSONResponse({"error": "❌ PDF enthält keinen extrahierbaren Text."}, status_code=400)

        # 🟢 Prompt für KPRIM-Fragen:
        prompt = f"""
Du bist ein Prüfungsersteller an einer Hochschule. Erstelle {num_questions} KPRIM-Prüfungsfragen (Multiple-Choice mit 4 Aussagen).
Wichtig:
- Zu jeder Frage soll es genau 4 Aussagen geben.
- Markiere für jede Aussage klar, ob sie 'richtig' oder 'falsch' ist.
- Formatiere die Ausgabe als JSON:
[
  {{
    "frage": "Frage 1 Text",
    "aussagen": [
      {{ "text": "Aussage 1", "correct": true }},
      {{ "text": "Aussage 2", "correct": false }},
      ...
    ]
  }},
  ...
]
Nutze als Grundlage den folgenden Text:
{text[:3000]}
        """

        completion = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        raw_output = completion.choices[0].message.content.strip()

        # Versuche JSON zu parsen:
        try:
            questions = json.loads(raw_output)
        except json.JSONDecodeError as decode_err:
            return JSONResponse({"error": f"❌ Fehler beim Parsen der GPT-Antwort als JSON: {decode_err}", "raw_output": raw_output}, status_code=500)

        return JSONResponse({"questions": questions})

    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der KPRIM-Fragen: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# -----------------------------------------------
# 🚀 Lückentext Endpoint (Prüfungsmodus)
# -----------------------------------------------



load_dotenv()

client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger("main")

# ✅ Session Middleware für User-Session-Handling:
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "supersecretkey"))

@app.get("/lueckentext")
async def lueckentext_page():
    return FileResponse("static/lueckentext.html")


@app.post("/generate_lueckentext")
async def generate_lueckentext(
    request: Request,
    file: UploadFile = Form(...),
    num_questions: int = Form(...),
    difficulty: str = Form(...)
):
    try:
        contents = await file.read()
        reader = PdfReader(io.BytesIO(contents))
        text = "\n".join([page.extract_text() or "" for page in reader.pages])

        if not text.strip():
            return JSONResponse({"error": "❌ PDF enthält keinen extrahierbaren Text."}, status_code=400)

        # Prompt an GPT-4:
        prompt = f"""
Du bist ein Lerncoach und erstellst interaktive Lückentext-Fragen.
Finde {num_questions} Begriffe als Lücken im Text mit dem Schwierigkeitsgrad: {difficulty}.

Für jede Aufgabe:
- Gib für jede Frage zusätzlich den Schwierigkeitsgrad ('einfach', 'mittel', 'schwer') an.
- Gib den Satz als Lückentext zurück (markiere die Lücke mit drei Unterstrichen ___).
- Nenne die korrekte Antwort (das fehlende Wort).
- Gib eine **knappe, einfach verständliche Definition**.
- Gib **ein praktisches, greifbares Beispiel**: Das Beispiel sollte zeigen, wie der Begriff in der Praxis verwendet wird (z.B. in einem Unternehmen, Alltag, Projekt, etc.). Vermeide zu abstrakte Formulierungen wie „zur Verdeutlichung von X“.

Format:
[
  {{
    "text": "Hier ist der Lückentext mit ___",
    "answer": "Begriff",
    "definition": "Kurz und einfach erklärt.",
    "difficulty": "einfach"  # oder "mittel" oder "schwer",
    "example": "Praxisbeispiel oder Anwendungsszenario."
  }},
  ...
]

Nutze diesen Text:
{text[:3000]}
"""

        completion = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        raw_output = completion.choices[0].message.content.strip()

        try:
            questions = json.loads(raw_output)
        except json.JSONDecodeError as decode_err:
            logger.error(f"❌ Fehler beim Parsen der GPT-Antwort als JSON: {decode_err}")
            return JSONResponse({
                "error": f"❌ Fehler beim Parsen der GPT-Antwort als JSON: {decode_err}",
                "raw_output": raw_output
            }, status_code=500)

        # Begriffe zufällig durchmischen:
        random.shuffle(questions)

        # Session speichern:
        session_data = {str(idx): q for idx, q in enumerate(questions)}
        request.session['lueckentext_questions'] = session_data

        # Lückentext-HTML generieren:
        lueckentext_html = "".join([
            f"<p>{q['text'].replace('___', f'<span class=\"blank\" data-position=\"{idx}\">___</span>')}</p>"
            for idx, q in enumerate(questions)
        ])
        terms = [q['answer'] for q in questions]
        random.shuffle(terms)

        return JSONResponse({
            "lueckentext": lueckentext_html,
            "terms": terms
        })

    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der Lückentext-Aufgaben: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

class CheckAnswerRequest(BaseModel):
    term: str
    position: str

@app.post("/check_lueckentext")
async def check_lueckentext(
    request: Request,
    payload: CheckAnswerRequest
):
    try:
        # Hole die gespeicherten Fragen aus der Session
        questions = request.session.get('lueckentext_questions', {})

        # Suche die richtige Frage anhand der Position
        question = questions.get(str(payload.position))

        if not question:
            return JSONResponse({"error": "❌ Keine Frage gefunden für diese Position."}, status_code=400)

        # Vergleiche Antwort
        correct_answer = question['answer'].strip().lower()
        user_answer = payload.term.strip().lower()
        correct = (user_answer == correct_answer)

        logger.info(f"Antwort geprüft: User → '{user_answer}' | Richtig → '{correct_answer}' | Ergebnis: {correct}")

        return JSONResponse({
            "correct": correct,
            "definition": question['definition'],
            "example": f"Beispiel zur Verdeutlichung von '{question['answer']}'."
        })

    except Exception as e:
        logger.error(f"❌ Fehler beim Überprüfen der Lückentext-Antwort: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# -----------------------------------------------
# 🚀 Challenge-Mode
# -----------------------------------------------

LEVELS = ["Intro", "Quiz", "Speed Challenge", "Open Questions", "Final Mini-Game"]

@app.get("/challenge")
async def challenge_page():
    return FileResponse("static/challenge_mode.html")

@app.post("/upload_pdf")
async def upload_pdf(request: Request, file: UploadFile = Form(...)):
    contents = await file.read()
    reader = PdfReader(io.BytesIO(contents))
    text = "\n".join([page.extract_text() or "" for page in reader.pages])

    if not text.strip():
        return JSONResponse({"error": "❌ PDF enthält keinen extrahierbaren Text."}, status_code=400)

    # 🔥 Temp-Ordner erstellen, falls nicht vorhanden
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # 📝 Lokale Text-Datei erstellen
    file_id = str(uuid.uuid4())
    file_path = os.path.join(temp_dir, f"{file_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    # 🔥 Nur Dateipfad merken
    request.session['pdf_text_path'] = file_path
    request.session['level'] = 0
    request.session['start_time'] = time.time()
    request.session['hints_used'] = 0
    request.session['points'] = 0

    logger.info(f"✅ Lerntext gespeichert unter: {file_path}")

    return JSONResponse({
        "message": "✅ PDF erfolgreich hochgeladen!",
        "level": LEVELS[0],
        "text_preview": text[:200]
    })




@app.post("/generate_level")
async def generate_level(request: Request):
    try:
        data = await request.json()
    except:
        data = {}

    level = data.get("level", request.session.get("level", 0))
    request.session["level"] = level
    file_path = request.session.get("pdf_text_path", "")

    if not os.path.exists(file_path):
        return JSONResponse({"error": "❌ Lerntext-Datei nicht gefunden."}, status_code=400)

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    if level == 0:
        prompt = f"""
Du bist ein Lernavatar. Bevor wir mit dem Lernspiel starten, gib bitte eine freundliche und motivierende Zusammenfassung des folgenden Textes.

**Wichtig**:
- Dein Antworttext beschreibt den Lerninhalt.
- Verwende Absätze mit `<p>...</p>`.
- Wichtige Begriffe innerhalb deines Textes bitte fett mit `<strong>...</strong>`.
- Für freundliche Motivationssätze verwende `<em>...</em>`.
- Sprich die Nutzerin/den Nutzer direkt an ("Du schaffst das!").

Hier ist der Text:
{text[:3000]}
"""

        avatar_message = await generate_avatar_response(prompt)
        return JSONResponse({"avatar_message": avatar_message, "level": LEVELS[level]})

    elif level == 1:
        try:
            questions = await generate_quiz_questions(text)
            if not isinstance(questions, list) or not all("question" in q and "options" in q for q in questions):
                logger.error(f"❌ Ungültige Fragenstruktur: {questions}")
                return JSONResponse({"error": "❌ Die generierten Fragen sind ungültig oder unvollständig."}, status_code=500)

            request.session['questions_level1'] = questions
            return JSONResponse({"questions": questions, "level": LEVELS[level]})
        except Exception as e:
            logger.error(f"❌ Fehler bei Level 1-Generierung: {e}")
            return JSONResponse({"error": f"Fehler bei der Quiz-Generierung: {e}"}, status_code=500)

    elif level == 2:
        terms = await extract_terms(text)
        request.session['speed_terms'] = terms
        return JSONResponse({"terms": terms, "level": LEVELS[level]})

    elif level == 3:
        open_questions = await generate_open_questions(text)
        request.session['open_questions'] = open_questions
        return JSONResponse({"questions": open_questions, "level": LEVELS[level]})

    elif level == 4:
        return JSONResponse({"minigame": "🎉 Mini-Game Platzhalter", "level": LEVELS[level]})

async def generate_avatar_response(prompt):
    completion = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()

async def generate_quiz_questions(text: str):
    snippet = text[:3000]  # 🧠 Reduziere auf die ersten 3000 Zeichen (ca. 1–2 Seiten)

    prompt = f"""
Du bist ein Professor für Wirtschaftsinformatik und möchtest ein Quiz zu folgendem Lerntext erstellen.

Erstelle bitte **6 Quizfragen** im Multiple-Choice-Format:
- 2 leichte Fragen
- 2 mittlere Fragen
- 2 schwierige Fragen

Wichtig:
- Gib zu jeder Frage genau 4 Antwortoptionen.
- Gib die richtige Antwort immer korrekt wieder.
- Formatiere die Ausgabe als JSON im folgenden Format:

[
  {{
    "question": "Frage 1",
    "options": ["A", "B", "C", "D"],
    "answer": "C"
  }},
  ...
]

Hier ist der Lerntext:
\"\"\"
{snippet}
\"\"\"
"""

    completion = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return json.loads(completion.choices[0].message.content.strip())
    except json.JSONDecodeError as e:
        logger.error(f"❌ Fehler beim Parsen der Quizfragen: {e}")
        raise e


async def extract_terms(text):
    prompt = f"Finde 10 wichtige Begriffe, die gut für eine Speed-Challenge geeignet sind. Text: {text}"
    completion = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(completion.choices[0].message.content.strip())

async def generate_open_questions(text):
    prompt = f"Erstelle 5 offene Fragen zum folgenden Lerntext: {text}"
    completion = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(completion.choices[0].message.content.strip())

@app.post("/next_level")
async def next_level(request: Request):
    current_level = request.session.get("level", 0)
    if current_level < len(LEVELS) - 1:
        request.session['level'] += 1
        return JSONResponse({"message": f"🎉 Level {current_level + 1} abgeschlossen! Nächstes Level: {LEVELS[current_level + 1]}"})
    else:
        total_time = time.time() - request.session.get("start_time", time.time())
        hints = request.session.get("hints_used", 0)
        points = request.session.get("points", 0)
        return JSONResponse({
            "message": "🎉 Challenge abgeschlossen!",
            "total_time": total_time,
            "hints_used": hints,
            "points": points
        })

@app.post("/generate_speed_challenge")
async def generate_speed_challenge(request: Request):
    try:
        questions_data = request.session.get('lueckentext_questions', {})
        if not questions_data:
            return JSONResponse({"error": "❌ Keine gespeicherten Fragen in der Session."}, status_code=400)

        # Fragen nach Schwierigkeit sortieren
        questions_by_difficulty = {
            "einfach": [q for q in questions_data.values() if q.get("difficulty") == "einfach"],
            "mittel": [q for q in questions_data.values() if q.get("difficulty") == "mittel"],
            "schwer": [q for q in questions_data.values() if q.get("difficulty") == "schwer"]
        }

        # Wähle 2 pro Schwierigkeitsgrad, wenn genug da sind:
        selected = []
        for level, amount in [("einfach", 2), ("mittel", 2), ("schwer", 2)]:
            pool = questions_by_difficulty[level]
            if len(pool) < amount:
                amount = len(pool)
            selected += random.sample(pool, amount)

        challenge_questions = []
        for q in selected:
            options = [q['answer']]
            other_answers = [x['answer'] for x in questions_data.values() if x['answer'] != q['answer']]
            options += random.sample(other_answers, min(3, len(other_answers)))
            random.shuffle(options)

            challenge_questions.append({
                "text": q['text'].replace("___", "_________"),
                "answer": q['answer'],
                "definition": q['definition'],
                "difficulty": q['difficulty'],
                "options": options
            })

        return JSONResponse(challenge_questions)

    except Exception as e:
        logger.error(f"❌ Fehler beim Generieren der Speed-Challenge: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/generate_open_questions")
async def generate_open_questions(request: Request):
    try:
        questions_data = request.session.get('lueckentext_questions', {})
        if not questions_data:
            return JSONResponse({"error": "❌ Keine gespeicherten Fragen in der Session."}, status_code=400)

        # Gleiches Prinzip: 2 einfach, 2 mittel, 2 schwer
        questions_by_difficulty = {
            "einfach": [q for q in questions_data.values() if q.get("difficulty") == "einfach"],
            "mittel": [q for q in questions_data.values() if q.get("difficulty") == "mittel"],
            "schwer": [q for q in questions_data.values() if q.get("difficulty") == "schwer"]
        }

        selected = []
        for level, amount in [("einfach", 2), ("mittel", 2), ("schwer", 2)]:
            pool = questions_by_difficulty[level]
            if len(pool) < amount:
                amount = len(pool)
            selected += random.sample(pool, amount)

        open_questions = [
            {
                "question": q['text'].replace("___", "_________"),
                "answer": q['answer'],
                "definition": q['definition'],
                "difficulty": q['difficulty']
            }
            for q in selected
        ]

        return JSONResponse(open_questions)

    except Exception as e:
        logger.error(f"❌ Fehler beim Generieren der offenen Fragen: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

class OpenQuestionCheckRequest(BaseModel):
    question_index: int
    user_answer: str
    hint_used: bool = False  # Damit Hints gezählt werden

@app.post("/check_open_question")
async def check_open_question(request: Request, payload: OpenQuestionCheckRequest):
    try:
        questions = request.session.get('open_questions', [])
        if not questions or payload.question_index >= len(questions):
            return JSONResponse({"error": "❌ Keine Frage gefunden für diese Position."}, status_code=400)

        question = questions[payload.question_index]
        correct_answer = question['answer'].strip().lower()
        user_answer = payload.user_answer.strip().lower()

        # 🎯 80%-Matching
        similarity = fuzz.token_sort_ratio(user_answer, correct_answer)
        is_correct = similarity >= 80

        # Punkte & Hints verwalten
        if 'points' not in request.session:
            request.session['points'] = 0
        if 'hints_used' not in request.session:
            request.session['hints_used'] = 0

        if payload.hint_used:
            request.session['hints_used'] += 1

        if is_correct:
            request.session['points'] += 1

        feedback = {
            "correct": is_correct,
            "similarity": similarity,
            "correct_answer": question['answer'],
            "definition": question['definition'],
            "example": question.get('example', "Kein Beispiel vorhanden.")
        }

        if not is_correct:
            feedback['avatar_feedback'] = (
                f"❌ Nicht ganz korrekt! Die Musterlösung wäre: '{question['answer']}'. "
                f"Definition: {question['definition']}."
            )
        else:
            feedback['avatar_feedback'] = "✅ Sehr gut! Deine Antwort war korrekt genug."

        return JSONResponse(feedback)

    except Exception as e:
        logger.error(f"❌ Fehler beim Überprüfen der offenen Antwort: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# -----------------------------------------------
# 🚀 Memory-Game
# -----------------------------------------------
@app.post("/generate_memory_cards")
async def generate_memory_cards(request: Request):
    text = request.session.get("learning_text", "")
    if not text:
        return JSONResponse({"error": "❌ Kein Lerntext vorhanden. PDF zuerst hochladen!"}, status_code=400)

    prompt = f"""
Erstelle 5 Memory-Paare auf Basis des folgenden Lerntexts.
Jedes Paar besteht aus:
1. Einem Fachbegriff.
2. Einer kurzen passenden Erklärung oder Synonym.

Formatiere das Ergebnis so:
[
  {{"id": 1, "text": "IT Governance"}},
  {{"id": 1, "text": "Steuerung von IT"}},
  ...
]

Text:
{text[:3000]}
"""

    completion = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        memory_cards = json.loads(completion.choices[0].message.content.strip())
    except json.JSONDecodeError as e:
        return JSONResponse({"error": f"Fehler beim Parsen: {e}"}, status_code=500)

    return JSONResponse(memory_cards)





# -----------------------------------------------
# 🚀 Uvicorn Start
# -----------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
