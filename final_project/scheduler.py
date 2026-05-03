from models import Doctor, Appointment, db
from datetime import datetime, timedelta

def get_available_doctor(department):
    # Find first doctor in department
    doctor = Doctor.query.filter_by(specialty=department).first()
    if not doctor:
        doctor = Doctor.query.first()  # fallback
    return doctor

def get_next_available_time(doctor_id, day, base_time):
    # Check every 10 minutes from base_time until a free slot is found
    for i in range(0, 12):  # up to 2 hours
        hour, minute = map(int, base_time.split(':'))
        minute += i * 10
        hour += minute // 60
        minute = minute % 60
        time_slot = f"{str(hour).zfill(2)}:{str(minute).zfill(2)}"
        existing = Appointment.query.filter_by(doctor_id=doctor_id, day=day, time_slot=time_slot).first()
        if not existing:
            return time_slot
    return None  # No slot available

def get_next_available_day(patient_id):
    # Find the next day without an appointment for this patient
    day_offset = 1
    while True:
        day = (datetime.utcnow() + timedelta(days=day_offset)).strftime('%Y-%m-%d')
        existing = Appointment.query.filter_by(patient_id=patient_id, day=day).first()
        if not existing:
            return day
        day_offset += 1

def schedule_appointment(patient_id, department, urgency, selected_day=None):
    doctor = get_available_doctor(department)
    if not doctor:
        return None
    # Use selected_day if provided, else next available day
    if selected_day:
        day = selected_day
        # If patient already has appointment on this day, find next available
        existing = Appointment.query.filter_by(patient_id=patient_id, day=day).first()
        if existing:
            day = get_next_available_day(patient_id)
    else:
        day = get_next_available_day(patient_id)
    # Check if max appointments reached for the day
    appt_count = Appointment.query.filter_by(day=day).count()
    if appt_count >= 30:
        return None  # No more slots available for this day
    # Assign base time by urgency
    if urgency == 'high':
        base_time = '09:00'
    elif urgency == 'medium':
        base_time = '10:00'
    else:
        base_time = '11:00'
    time_slot = get_next_available_time(doctor.doctor_id, day, base_time)
    if not time_slot:
        return None
    appt = Appointment(
        patient_id=patient_id,
        doctor_id=doctor.doctor_id,
        day=day,
        time_slot=time_slot,
        urgency_level=urgency
    )
    db.session.add(appt)
    db.session.commit()
    return appt
