# SymptoSense AI

An agentic autonomous patient scheduling and triage system using Flask, SQLAlchemy, and simple NLP.

## Features
- Symptom analysis and urgency detection (NLP, rule-based)
- Autonomous appointment scheduling based on urgency and doctor availability
- Patient history tracking
- Doctor management
- Professional frontend (HTML/CSS/JS)
- No external APIs required

## Setup
1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
2. Run the app:
   ```powershell
   python app.py
   ```
3. Open [http://localhost:5000](http://localhost:5000) in your browser.

## Project Structure
- `app.py`: Flask backend
- `models.py`: Database models
- `nlp.py`: Symptom analysis logic
- `scheduler.py`: Appointment scheduling logic
- `templates/index.html`: Frontend
- `requirements.txt`: Python dependencies

## Notes
- Data is stored in `symptosense.db` (SQLite)
- Doctors are auto-populated on first run
- No external APIs used
