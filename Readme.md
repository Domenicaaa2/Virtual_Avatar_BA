# 🧑‍🏫 Virtueller Dozent – Interaktive Lernplattform mit KI-Unterstützung

**Ein Prototyp im Rahmen der Bachelorarbeit von Nina Habegger, ZHAW SML (2025)**

Dieses Projekt bildet den praktischen Teil der Bachelorarbeit _„Akzeptanz und Potenzial virtueller Dozenten an Hochschulen“_ und stellt einen ersten, funktionsfähigen Prototyp dar. Ziel war es, ein KI-gestütztes Lernsystem zu entwickeln, das verschiedene Aufgabenformate anbietet und auf natürliche Weise mit Lernenden interagiert.

Die gesamte technische Umsetzung sowie der didaktische Einsatz werden in **Kapitel 5 der Arbeit** detailliert beschrieben.

---

## ⚠️ Hinweise

- Sollte das System hängen bleiben oder nicht korrekt antworten, hilft meist ein **einfacher Seiten-Refresh**.
- In seltenen Fällen können **lokale Sessions** zu Konflikten führen.
- 🗣️ **Die gesprochene Antwort des Avatars kann vom angezeigten Text leicht abweichen**, da Text-to-Speech und Textverarbeitung getrennt generiert werden. Dies wurde zur realistischen Synchronisation bewusst in Kauf genommen.

---

## ⚙️ Voraussetzungen

### 🔐 .env-Konfiguration

Lege im Hauptverzeichnis eine Datei mit dem Namen `.env` an und trage folgende Werte ein:

```env
OPENAI_API_KEY=           # OpenAI API Key (für GPT-Modelle)
HEYGEN_API_KEY=           # HeyGen API Key (für Avatar-Video)
AVATAR_ID=                # Avatar-ID (z. B. "June_HR_public")
VOICE_ID=                 # Sprach-ID für TTS
SESSION_SECRET_KEY=       # Sicherheitsschlüssel für Sessions
```

Ohne gültige API-Keys funktionieren zentrale Komponenten wie Sprachverarbeitung oder Videoantworten nicht.

---

## 🛠️ Installation & Ausführung

### 1. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 2. Lokalen Server starten

```bash
python main.py
```

### 3. Anwendung im Browser öffnen

Empfohlene Startseite:

```
http://localhost:5000/avatar_player
```

---

## 📂 Modulübersicht

### 🎤 avatar_player.html

- Zentrale Lernumgebung mit KI-Avatar
- Nutzer:innen stellen Fragen (Text oder Sprache)
- GPT-4 generiert Antworten + HeyGen-Videoausgabe
- Punktesystem mit motivierendem Feedback
- Badges als Belohnung bei Fortschritt  
✅ **Kernmodul des Prototyps**

---

### 📘 flashcards.html

- Karteikarten-Modus zur Wissensfestigung
- Begriff & Definition werden angezeigt
- Auswahlmöglichkeit (richtig/falsch)
- Falsch beantwortete Karten rotieren zur Wiederholung

---

### ❓ kprim.html

- KPRIM-Prüfungsformat mit vier Aussagen pro Frage
- Nutzer:innen bewerten jede Aussage als richtig/falsch
- Nur bei 100 % korrekter Auswahl gibt es Punkte
- Avatar gibt Feedback per Video

---

### ✍️ lueckentext.html

- PDF-Upload mit Lückentext-Generierung
- Auswahl von Anzahl & Schwierigkeitsgrad
- Begriffe via Drag & Drop einsetzen
- Rückmeldung mit Definition und Beispiel
- Punkte + Badge-Fortschritt

---

### 🕹️ challenge_mode.html _(experimentell)_

- Spielbasierter Zeitmodus (Prototyp unvollständig)
- Aktuell nicht voll funktionsfähig
- Diente als explorativer Test für Spielmechaniken
- Ideen: Countdown, Aufgabenrotation, Levelsystem

---

## 📄 Hinweis zur Bachelorarbeit

Dieses Projekt wurde im Rahmen der Bachelorarbeit im Studiengang **Wirtschaftsinformatik** an der **ZHAW School of Management and Law** entwickelt.  
Technische Hintergründe, didaktisches Konzept sowie empirische Erkenntnisse findest du in der schriftlichen Arbeit (Kapitel 5).

---

## 🧠 Autorin

**Nina Habegger**  
ZHAW School of Management and Law  
Bachelorarbeit | Wirtschaftsinformatik | 2025  
📫 habegnin@students.zhaw.ch
