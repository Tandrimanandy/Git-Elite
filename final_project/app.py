# Place endpoint after app and db initialization, before main block

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from db import db
from models_urban import Hospital, UrbanDoctor, DiseaseOccurrence, MedicalFacility, init_db, populate_sample_data
# Place endpoint after app initialization
from models import db, Patient, Doctor, Appointment, PatientHistory, User
from nlp import analyze_symptoms
from scheduler import schedule_appointment
import os
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///symptosense.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'symptosense-secret-key-2024'
db.init_app(app)

# ---------- Auth helper ----------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ---------- Auth routes ----------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('index'))
    error = None
    email_val = ''
    if request.method == 'POST':
        email_val = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not email_val or not password:
            error = 'Email and password are required.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif User.query.filter_by(email=email_val).first():
            error = 'An account with this email already exists.'
        if not error:
            user = User(email=email_val)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            session['user_email'] = user.email
            return redirect(url_for('index'))
    return render_template('signup.html', error=error, email=email_val)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    error = None
    email_val = ''
    if request.method == 'POST':
        email_val = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email_val).first()
        if not user or not user.check_password(password):
            error = 'Invalid email or password.'
        else:
            session['user_id'] = user.id
            session['user_email'] = user.email
            return redirect(url_for('index'))
    return render_template('login.html', error=error, email=email_val)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))






# Doctor Dashboard: Get all appointments for a specific doctor
@app.route('/doctor/<int:doctor_id>/appointments')
def doctor_appointments(doctor_id):
    from scheduler import Appointment
    appts = Appointment.query.filter_by(doctor_id=doctor_id).all()
    result = []
    for appt in appts:
        result.append({
            'appointment_id': appt.appointment_id,
            'patient_id': appt.patient_id,
            'day': appt.day,
            'time_slot': appt.time_slot,
            'status': appt.status
        })
    return jsonify(result)

# Simple AI-powered chatbot endpoint (local logic)
@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    # Accept both 'question' and 'message' for compatibility
    user_msg = data.get('question') or data.get('message') or ''
    user_msg = user_msg.strip()
    print(f"[Chatbot] Received: {user_msg}")
    if not user_msg:
        print("[Chatbot] No message provided.")
        return jsonify({'reply': "Please enter a question or symptom."})
    # Website guidance logic (improved matching)
    navigation_map = {
        'appointments': [
            (['book', 'schedule', 'make'], "To book an appointment, go to the 'Appointments' tab, select your preferred date, and follow the instructions to schedule your visit."),
            (['check', 'view', 'my', 'details'], "To check your appointment details, go to the 'Appointments' tab and enter your Patient ID or select the date. You will see your scheduled appointments and their details."),
            (['cancel', 'delete', 'remove'], "Currently, appointments can only be canceled by contacting the hospital directly or through the 'Appointments' tab if the option is available.")
        ],
        'history': [
            (['view', 'my', 'medical'], "To view your patient history, click on the 'Patient History' tab and enter your Patient ID. You'll see your previous symptoms and appointments.")
        ],
        'symptom checker': [
            (['check', 'analyze', 'analysis'], "To check your symptoms, use the 'Symptom Checker' tab. Fill in your details and describe your symptoms for an AI-powered analysis.")
        ],
        'doctors': [
            (['find', 'list', 'available', 'info'], "To see available doctors, visit the 'Doctors' tab. You can view their specialties and hospital information.")
        ],
        'hospitals': [
            (['find', 'list', 'info', 'details'], "The 'Hospitals' tab lists hospitals and their specializations. You can check doctor availability and facility details.")
        ],
        'medical facilities': [
            (['facilities', 'available'], "The 'Medical Facilities Available' tab shows what facilities each hospital offers.")
        ],
        'disease tracker': [
            (['disease', 'stats', 'chart', 'statistics'], "The 'Disease Tracker' tab displays statistics and charts about disease occurrences in the area.")
        ],
        'general': [
            (['how to use', 'help', 'guide', 'navigation', 'features'], "This website helps you check symptoms, book appointments, view your medical history, find doctors and hospitals, and track disease statistics. Use the sidebar to navigate between features.")
        ]
    }
    user_msg_lower = user_msg.lower()
    # Flexible phrase matching for navigation
    navigation_phrases = [
        (['schedule appointment', 'book appointment', 'make appointment'], "To schedule an appointment, go to the 'Appointments' tab, select your preferred date, and follow the instructions to book your visit."),
        (['see appointments', 'view appointments', 'check appointments', 'my appointments'], "To see your appointments, go to the 'Appointments' tab in the sidebar. You can filter by date or see all your scheduled appointments."),
        (['see patient history', 'view patient history', 'my history', 'medical history'], "To see patient history, click on the 'Patient History' tab and enter your Patient ID. You'll see your previous symptoms and appointments."),
        (['cancel appointment', 'delete appointment', 'remove appointment'], "Currently, appointments can only be canceled by contacting the hospital directly or through the 'Appointments' tab if the option is available."),
        (['use symptom checker', 'symptom checker', 'analyze symptoms', 'check symptoms'], "To check your symptoms, use the 'Symptom Checker' tab. Fill in your details and describe your symptoms for an AI-powered analysis."),
        (['find doctor', 'doctor list', 'available doctors', 'doctor info'], "To see available doctors, visit the 'Doctors' tab. You can view their specialties and hospital information."),
        (['find hospital', 'hospital list', 'hospital info', 'hospital details'], "The 'Hospitals' tab lists hospitals and their specializations. You can check doctor availability and facility details."),
        (['disease stats', 'disease tracker', 'disease chart', 'disease statistics'], "The 'Disease Tracker' tab displays statistics and charts about disease occurrences in the area.")
    ]
    import difflib
    user_words = user_msg_lower.split()
    for keywords, reply in navigation_phrases:
        for kw in keywords:
            # Fuzzy match: check if any word in user input is close to a keyword
            for user_word in user_words:
                if difflib.SequenceMatcher(None, user_word, kw.split()[0]).ratio() > 0.8:
                    print(f"[Chatbot] Fuzzy matched '{user_word}' to '{kw}' for reply: '{reply}'")
                    return jsonify({'reply': reply})
            # Also check if the keyword is a substring (for exact matches)
            if kw in user_msg_lower:
                print(f"[Chatbot] Matched keyword: '{kw}' for reply: '{reply}'")
                return jsonify({'reply': reply})

    # Improved navigation intent: require at least 2 keyword matches for a pattern
    for section, patterns in navigation_map.items():
        for keywords, answer in patterns:
            match_count = sum(1 for kw in keywords if kw in user_msg_lower)
            if match_count >= 2:
                print(f"[Chatbot] Matched section: '{section}' with {match_count} keywords for answer: '{answer}'")
                return jsonify({'reply': answer})
    # Basic intent detection for symptoms
    from nlp import analyze_symptoms
    symptom_keywords = ['symptom', 'feel', 'pain', 'sick', 'unwell', 'hurt', 'ache', 'feeling', 'health', 'problem']
    if any(kw in user_msg_lower for kw in symptom_keywords):
        urgency, dept = analyze_symptoms(user_msg)
        reply = f"Based on your description, urgency is '{urgency.capitalize()}' and suggested department is '{dept}'. "
        if urgency == 'high':
            reply += "Please seek immediate medical attention or visit the emergency department."
        elif urgency == 'medium':
            reply += "You should schedule an appointment soon."
        else:
            reply += "Your symptoms seem non-urgent, but monitor your condition and consult a doctor if needed."
        return jsonify({'reply': reply})
    # General health tips
    health_tips = [
        "Stay hydrated and eat a balanced diet.",
        "Wash your hands regularly to prevent infections.",
        "Get enough sleep and exercise regularly.",
        "If you feel unwell, consult a healthcare professional.",
        "Take medications only as prescribed by your doctor."
    ]
    if 'tip' in user_msg_lower or 'advice' in user_msg_lower:
        import random
        return jsonify({'reply': random.choice(health_tips)})
    # Default fallback
    return jsonify({'reply': "I'm here to help with health questions, symptoms, and guide you through the website. Ask me about appointments, history, doctors, or any feature!"})


# Initialize DB and populate sample data on startup
def initialize_and_populate():
    with app.app_context():
        db.create_all()
        populate_sample_data()  # Always repopulate sample data

initialize_and_populate()

def setup_db():
    with app.app_context():
        db.create_all()
        # Add sample doctors if not present
        if Doctor.query.count() == 0:
            doctors = [
                Doctor(name='Dr. Ankita Dutta', specialty='Cardiology', room_number='101'),
                Doctor(name='Dr. Tanu Nandy', specialty='Pulmonology', room_number='102'),
                Doctor(name='Dr. Deep Mondal', specialty='Neurology', room_number='103'),
                Doctor(name='Dr. Debasish Das', specialty='Orthopedics', room_number='104'),
                Doctor(name='Dr. Rohan Mullick', specialty='General', room_number='105'),
            ]
            db.session.bulk_save_objects(doctors)
            db.session.commit()

@app.route('/')
@login_required
def index():
    return render_template('index.html', user_email=session.get('user_email', ''))

@app.route('/submit_symptoms', methods=['POST'])
def submit_symptoms():
    data = request.get_json()
    name = data.get('name')
    symptoms = data.get('symptoms')
    date = data.get('date')
    if not name or not symptoms or not date:
        return jsonify({'status': 'error', 'message': 'Missing name, symptoms, or date'}), 400
    # Check if patient with same name and date exists
    patient = Patient.query.filter_by(name=name).first()
    if not patient:
        patient = Patient(name=name)
        db.session.add(patient)
        db.session.commit()
    # NLP analysis
    urgency, department = analyze_symptoms(symptoms)
    # Disease stats update: try to match a disease from DiseaseOccurrence
    from models_urban import DiseaseOccurrence, update_disease_stats
    diseases = [d.disease_name.lower() for d in DiseaseOccurrence.query.all()]
    matched_disease = None
    for dname in diseases:
        if dname in symptoms.lower():
            matched_disease = dname
            break
    if matched_disease:
        update_disease_stats(matched_disease.capitalize())
    # Add to history (store report_date as selected date)
    from datetime import datetime
    try:
        report_date = datetime.strptime(date, '%Y-%m-%d')
    except Exception:
        report_date = datetime.utcnow()
    history = PatientHistory(patient_id=patient.patient_id, symptoms_reported=symptoms, report_date=report_date)
    db.session.add(history)
    db.session.commit()
    # Count available slots for the selected day
    from scheduler import Appointment
    max_per_day = 30
    appt_count = Appointment.query.filter_by(day=date).count()
    available_slots = max_per_day - appt_count if appt_count < max_per_day else 0
    # Schedule appointment for selected date
    # Find a doctor from any hospital with matching department
    from models_urban import UrbanDoctor, Hospital
    matching_doctors = UrbanDoctor.query.filter_by(specialty=department).all()
    import random
    if matching_doctors:
        chosen_doc = random.choice(matching_doctors)
        # Create and save a real Appointment record
        from scheduler import Appointment
        appt = Appointment(
            patient_id=patient.patient_id,
            doctor_id=chosen_doc.id,
            day=date,
            time_slot='09:00-10:00',
            status='Scheduled',
            urgency_level=urgency
        )
        db.session.add(appt)
        db.session.commit()
        hospital_name = None
        hospital = Hospital.query.get(chosen_doc.hospital_id)
        if hospital:
            hospital_name = hospital.name
        appointment_details = {
            'patient_id': patient.patient_id,
            'doctor_id': appt.doctor_id,
            'day': appt.day,
            'time_slot': appt.time_slot,
            'urgency_level': appt.urgency_level,
            'suggested_department': department,
            'available_slots': available_slots - 1 if available_slots > 0 else 0,
            'hospital_name': hospital_name
        }
        return jsonify({'status': 'success', 'appointment_details': appointment_details})
    else:
        return jsonify({'status': 'error', 'message': f'No available doctor for department {department}.', 'available_slots': available_slots}), 400

@app.route('/appointments')
def appointments():
    date = request.args.get('date')
    if date:
        appts = Appointment.query.filter_by(day=date).all()
    else:
        appts = Appointment.query.all()
    result = []
    from models_urban import UrbanDoctor, Hospital
    for appt in appts:
        hospital_name = None
        urban_doc = UrbanDoctor.query.filter_by(id=appt.doctor_id).first()
        if urban_doc and urban_doc.hospital:
            hospital_name = urban_doc.hospital.name
        result.append({
            'appointment_id': appt.appointment_id,
            'patient_id': appt.patient_id,
            'doctor_id': appt.doctor_id,
            'day': appt.day,
            'time_slot': appt.time_slot,
            'status': appt.status,
            'hospital_name': hospital_name
        })
    return jsonify(result)

@app.route('/urban/hospitals')
def get_hospitals():
    hospitals = Hospital.query.all()
    result = []
    for hosp in hospitals:
        # Count doctors per specialization
        spec_counts = {}
        for doc in hosp.doctors:
            spec_counts[doc.specialty] = spec_counts.get(doc.specialty, 0) + 1
        for spec, count in spec_counts.items():
            # For demo, required = 4 for all
            required = 4
            result.append({
                'name': hosp.name,
                'specialization': spec,
                'doctors': count,
                'required': required
            })
    return jsonify(result)

@app.route('/urban/doctors')
def get_doctors():
    doctors = Doctor.query.all()
    return jsonify([
        {
            'doctor_id': doc.id,
            'name': doc.name,
            'specialty': doc.specialty,
            'hospital': doc.hospital.name
        } for doc in doctors
    ])

@app.route('/urban/diseases')
def get_diseases():
    # Only count diseases from patient history, using synonyms/keywords
    from models_urban import DiseaseOccurrence
    from models import PatientHistory
    diseases = DiseaseOccurrence.query.all()
    # Map disease names to keywords/synonyms
    disease_keywords = {
        'Flu': ['flu', 'influenza', 'fever', 'cold', 'flue', 'fluu'],
        'Diabetes': ['diabetes', 'diabetis', 'diabetees', 'high blood sugar', 'hyperglycemia', 'diabities'],
        'Hypertension': ['hypertension', 'high blood pressure', 'hypertention', 'hypertenion'],
        'COVID-19': ['covid', 'coronavirus', 'covid-19', 'sars-cov-2', 'covd', 'covidd'],
        'Asthma': ['asthma', 'wheezing', 'shortness of breath', 'azthma', 'asthama'],
        'Malaria': ['malaria', 'plasmodium', 'chills', 'sweating', 'maleria', 'malaira']
    }
    import difflib
    result = {d.disease_name: 0 for d in diseases}
    all_histories = PatientHistory.query.all()
    for history in all_histories:
        symptoms = history.symptoms_reported.lower()
        for dname, keywords in disease_keywords.items():
            # Fuzzy match: check for close matches in symptoms
            found = False
            for kw in keywords:
                if kw in symptoms:
                    found = True
                    break
                # Fuzzy match for words in symptoms
                for word in symptoms.split():
                    if difflib.SequenceMatcher(None, word, kw).ratio() > 0.85:
                        found = True
                        break
                if found:
                    break
            if found:
                result[dname] += 1
    # Always return all diseases, even those with zero count, for better chart output
    return jsonify([
        {'name': k, 'count': v} for k, v in result.items()
    ])

@app.route('/doctors')
def doctors():
    docs = Doctor.query.all()
    urban_docs = None
    try:
        from models_urban import UrbanDoctor, Hospital
        urban_docs = UrbanDoctor.query.all()
    except Exception:
        urban_docs = []
    result = []
    # Add classic Doctor model doctors
    hospital_names = ['City Hospital', 'Metro Medical', 'Urban Health Center', 'Green Valley Hospital', 'Riverfront Medical']
    for idx, doc in enumerate(docs):
        hosp_name = hospital_names[idx] if idx < len(hospital_names) else 'City Hospital'
        result.append({
            'doctor_id': doc.doctor_id,
            'name': doc.name,
            'specialty': doc.specialty,
            'room_number': hosp_name
        })
    # Add UrbanDoctor model doctors
    for doc in urban_docs:
        hospital_name = None
        try:
            hospital = Hospital.query.get(doc.hospital_id)
            if hospital:
                hospital_name = hospital.name
        except Exception:
            hospital_name = None
        result.append({
            'doctor_id': doc.id,
            'name': doc.name,
            'specialty': doc.specialty,
            'room_number': hospital_name if hospital_name else 'N/A'
        })
    return jsonify(result)

@app.route('/history/<int:patient_id>')
def history(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'status': 'error', 'message': 'Patient not found', 'history': []})
    histories = PatientHistory.query.filter_by(patient_id=patient_id).order_by(PatientHistory.report_date.desc()).all()
    history_list = []
    for h in histories:
        # Find associated appointments
        appts = Appointment.query.filter_by(patient_id=patient_id).all()
        appt_list = []
        for appt in appts:
            appt_list.append({
                'appointment_id': appt.appointment_id,
                'doctor_id': appt.doctor_id,
                'day': appt.day,
                'time_slot': appt.time_slot,
                'status': appt.status
            })
        history_list.append({
            'report_date': h.report_date,
            'symptoms_reported': h.symptoms_reported,
            'associated_appointments': appt_list,
            'patient_name': patient.name
        })
    return jsonify({'status': 'success', 'history': history_list, 'patient_name': patient.name})

@app.route('/medical_facilities')
def medical_facilities():
    from models_urban import Hospital, MedicalFacility
    hospitals = Hospital.query.all()
    result = []
    for hosp in hospitals:
        facilities = MedicalFacility.query.filter_by(hospital_id=hosp.id).all()
        result.append({
            'hospital': hosp.name,
            'facilities': [f.name for f in facilities]
        })
    return jsonify(result)



# AI-powered Nutritionist endpoint
@app.route('/nutritionist', methods=['POST'])
def nutritionist():
    data = request.get_json()
    age = data.get('age')
    gender = data.get('gender')
    bmi = data.get('bmi')
    preferences = data.get('preferences', '').lower()  # e.g., 'vegetarian', 'non-veg', 'vegan', etc.
    advice = []
    # Basic validation
    if not age or not gender or not bmi:
        return jsonify({'status': 'error', 'message': 'Missing age, gender, or BMI'}), 400
    try:
        age = int(age)
        bmi = float(bmi)
    except Exception:
        return jsonify({'status': 'error', 'message': 'Invalid age or BMI'}), 400

    # Dietary restriction logic (personalized)
    if 'vegan' in preferences:
        advice.append("You follow a vegan diet. Focus on lentils, beans, tofu, whole grains, nuts, seeds, and a variety of fruits and vegetables. Consider B12, iron, and omega-3 supplementation.")
    elif 'vegetarian' in preferences:
        advice.append("You are vegetarian. Include dairy, eggs, legumes, whole grains, nuts, seeds, and plenty of fruits and vegetables. Ensure adequate protein and iron intake.")
    elif 'non-veg' in preferences or 'nonveg' in preferences or 'non vegetarian' in preferences or 'nonvegetarian' in preferences:
        advice.append("You eat non-vegetarian food. Balance lean meats, fish, eggs, dairy, whole grains, and vegetables. Limit red and processed meats for heart health.")
    elif preferences:
        advice.append(f"Dietary preference noted: {preferences.capitalize()}.")

    # BMI-based advice (personalized)
    if bmi < 18.5:
        advice.append("You are underweight for your height. Add more calorie-dense healthy foods like nuts, dairy, and whole grains. Consider consulting a nutritionist for a personalized plan.")
    elif 18.5 <= bmi < 25:
        advice.append("Your BMI is in the normal range. Maintain your weight with a balanced diet and regular exercise.")
    elif 25 <= bmi < 30:
        advice.append("You are overweight. Focus on portion control, increase physical activity, and limit sugary and fatty foods.")
    else:
        advice.append("You are in the obese range. Consult a healthcare provider for a tailored weight loss plan. Emphasize vegetables, lean proteins, and regular exercise.")

    # Age-based advice (personalized)
    if age < 18:
        advice.append("As a young person, ensure you get enough calcium, vitamin D, and protein for growth. Avoid fad diets and focus on healthy eating habits.")
    elif 18 <= age < 40:
        advice.append("Maintain a balanced diet, stay active, and manage stress for long-term health.")
    elif 40 <= age < 60:
        advice.append("Monitor your cholesterol, blood pressure, and blood sugar. Include fiber-rich foods and limit salt and sugar.")
    else:
        advice.append("For seniors, focus on calcium, vitamin D, fiber, and hydration. Monitor salt and sugar intake.")

    # Gender-based advice (personalized)
    if gender.lower() == 'female':
        if age < 50:
            advice.append("Females under 50 need more iron (especially if premenopausal), calcium, and folic acid. Include leafy greens, dairy, and fortified cereals.")
        else:
            advice.append("Postmenopausal females should focus on calcium, vitamin D, and heart-healthy fats.")
    elif gender.lower() == 'male':
        advice.append("Males should monitor red meat intake and include heart-healthy fats like olive oil, nuts, and fish.")

    # If no advice was added, provide a fallback
    if not advice:
        advice.append("Eat a balanced diet with a mix of proteins, whole grains, fruits, vegetables, and healthy fats. Adjust portions based on your activity level.")

    return jsonify({'status': 'success', 'advice': ' '.join(advice)})

if __name__ == '__main__':
    setup_db()
    app.run(debug=True)
