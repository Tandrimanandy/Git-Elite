import re

# Simple NLP for symptom analysis (no external APIs)
def analyze_symptoms(symptoms):
    symptoms = symptoms.lower()
    # Define keywords for urgency and department
    high_urgency = [
            'chest pain', 'difficulty breathing', 'severe', 'unconscious', 'bleeding', 'stroke', 'heart attack',
            'loss of consciousness', 'severe pain', 'shortness of breath', 'acute', 'collapse', 'paralysis',
            'severe injury', 'severe trauma', 'severe bleeding', 'severe allergic reaction', 'severe burn', 'severe shock'
        ]
    medium_urgency = [
            'fever', 'vomiting', 'pain', 'infection', 'fracture', 'persistent', 'moderate', 'swelling', 'dizziness',
            'injury', 'cough', 'headache', 'sore throat', 'diarrhea', 'rash', 'fatigue', 'mild', 'moderate pain', 'moderate injury'
        ]
    departments = {
        'cardiology': ['stroke','chest pain', 'palpitations', 'heart', 'angina', 'arrhythmia', 'cardiac', 'tachycardia', 'bradycardia'],
        'pulmonology': ['breathing', 'cough', 'asthma', 'lung', 'wheeze', 'breathless', 'pneumonia', 'copd', 'respiratory', 'sputum', 'shortness of breath'],
        'neurology': ['brain stroke', 'seizure', 'headache', 'nerve', 'paralysis', 'numbness', 'tingling', 'tremor', 'memory', 'confusion', 'migraine', 'dizziness', 'vertigo', 'weakness', 'loss of consciousness'],
        'orthopedics': ['fracture', 'bone', 'joint', 'sprain', 'arthritis', 'back pain', 'muscle', 'tendon', 'ligament', 'orthopedic', 'dislocation', 'swelling', 'injury', 'rib', 'rib damage', 'rib fracture', 'knee', 'knee pain', 'knee injury', 'knee swelling'],
        'general': ['fever', 'pain', 'infection', 'vomiting', 'rash', 'fatigue', 'diarrhea', 'sore throat', 'mild', 'moderate', 'persistent']
    }
    urgency = 'low'
    for kw in high_urgency:
        if kw in symptoms:
            urgency = 'high'
            break
    if urgency == 'low':
        for kw in medium_urgency:
            if kw in symptoms:
                urgency = 'medium'
                break
    # Department suggestion
    suggested_department = 'General'
    # Prioritize brain stroke for neurology if urgent
    if 'brain stroke' in symptoms and urgency == 'high':
        suggested_department = 'Neurology'
    else:
        for dept, kws in departments.items():
            for kw in kws:
                if kw in symptoms:
                    suggested_department = dept.capitalize()
                    break
            if suggested_department != 'General':
                break
    return urgency, suggested_department
