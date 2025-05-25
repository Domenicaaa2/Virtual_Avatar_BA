🧑‍🏫 Virtueller Dozent – Interaktive Lernplattform mit KI-Unterstützung
Ein Prototyp im Rahmen der Bachelorarbeit von Nina Habegger, ZHAW SML (2025)
Dieses Projekt bildet den praktischen Teil der Bachelorarbeit „Akzeptanz und Potenzial virtueller Dozenten an Hochschulen“ und stellt einen ersten, funktionsfähigen Prototyp dar. Ziel war es, ein KI-gestütztes Lernsystem zu entwickeln, das verschiedene Aufgabenformate anbietet und auf natürliche Weise mit Lernenden interagiert.

Die gesamte technische Umsetzung sowie der didaktische Einsatz werden in Kapitel 5 der Arbeit detailliert beschrieben.

⚠️ Hinweis: Sollte das System einmal hängen bleiben oder nicht korrekt antworten, hilft oft ein einfacher Seiten-Refresh. In seltenen Fällen kommt es durch lokale Sessions zu temporären Konflikten.
🗣️ Wichtig: Die gesprochene Antwort des Avatars kann vom angezeigten Text leicht abweichen, da Text-to-Speech- und Textverarbeitung getrennt generiert werden. Dies wurde zur Wahrung realistischer Synchronisierung im Prototyp bewusst in Kauf genommen.

⚙️ Voraussetzungen
Um den Prototyp lokal auszuführen, werden folgende Schritte benötigt:

🔐 .env-Konfiguration
Lege im Hauptverzeichnis eine .env-Datei an und trage dort folgende API-Schlüssel ein:

makefile
Kopieren
Bearbeiten
OPENAI_API_KEY=           # OpenAI API Key (für GPT-Modelle)
HEYGEN_API_KEY=           # HeyGen API Key (für Avatar-Video)
AVATAR_ID=                # Avatar-ID (z. B. "June_HR_public")
VOICE_ID=                 # Sprach-ID für TTS
SESSION_SECRET_KEY=       # Sicherheitsschlüssel für Sitzungen
Ohne gültige API-Keys funktionieren zentrale Funktionen wie Sprachverarbeitung oder Videoantworten nicht.

🛠️ Installation & Ausführung
1. Abhängigkeiten installieren
bash
Kopieren
Bearbeiten
pip install -r requirements.txt

2. Server starten
bash
Kopieren
Bearbeiten
python main.py
3. Anwendung im Browser öffnen
Empfohlen:
http://localhost:5000/avatar_player

📂 Modulübersicht
🎤 avatar_player.html
Zentrale Lernumgebung mit KI-Avatar

Nutzer:innen stellen Fragen (Text oder Sprache)

Antworten via GPT-4 + HeyGen-Video

Punktesystem mit motivierendem Feedback

Belohnung durch Badges bei Fortschritt

Hauptmodul des Prototyps

📘 flashcards.html
Karteikarten-Modus zur Wissensfestigung

Begriff & Definition werden angezeigt

Auswahlmöglichkeit (richtig/falsch)

Fehlerhafte Karten rotieren zur Wiederholung

❓ kprim.html
KPRIM-Prüfungsmodus

Pro Frage vier Aussagen

Lernende bewerten jede Aussage als richtig/falsch

Nur bei 100 % korrekter Auswahl gibt es Punkte

Feedback durch Videoantwort des Avatars

✍️ lueckentext.html
Lückentext-Modul mit PDF-Upload

Upload eigener PDFs mit Fachtexten

Auswahl von Anzahl & Schwierigkeitsgrad der Lücken

Begriffe via Drag & Drop einsetzen

Rückmeldung mit Definition & Beispiel

Punkte + Badges

🕹️ challenge_mode.html (experimentell)
Spielbasierter Zeitmodus (nicht vollständig umgesetzt)

Funktioniert derzeit nicht vollständig

Diente als explorativer Test für Spielmechaniken

Geplante Funktionen: Countdown, Aufgabenrotation, Levelsystem

📄 Hinweis zur Bachelorarbeit
Dieses Projekt wurde im Rahmen der Bachelorarbeit im Studiengang Wirtschaftsinformatik an der ZHAW entwickelt.
Die didaktische Konzeption, technischen Hintergründe und Ergebnisse der Akzeptanzmessung sind in der Arbeit umfassend dokumentiert.

🧠 Autorin
Nina Habegger
ZHAW School of Management and Law
Bachelorarbeit | Wirtschaftsinformatik | 2025
Kontakt: habegnin@students.zhaw.ch

