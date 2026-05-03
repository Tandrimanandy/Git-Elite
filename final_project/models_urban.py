
# Medical Facility model
from db import db
class MedicalFacility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)

# Models for hospitals, doctors, and disease tracking

from db import db

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    location = db.Column(db.String(128))
    doctors = db.relationship('UrbanDoctor', backref='hospital', lazy=True)

class UrbanDoctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    specialty = db.Column(db.String(64), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)

class DiseaseOccurrence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    disease_name = db.Column(db.String(128), nullable=False)
    count = db.Column(db.Integer, default=1)
    city = db.Column(db.String(128))

# Utility functions for shortages/excess
# ...existing code...

def init_db(app):
    """Initialize and create all tables."""
    db.init_app(app)
    with app.app_context():
        db.create_all()

def populate_sample_data():
    # Add 25 sample hospitals if not present
    if Hospital.query.count() < 25:
        hospital_names = [
            'City Hospital', 'Metro Medical', 'Urban Health Center', 'Green Valley Hospital', 'Riverfront Medical',
            'Sunrise Clinic', 'Lakeside Hospital', 'Hilltop Medical', 'Central Health', 'Westside Clinic',
            'Eastview Hospital', 'Northpoint Medical', 'Southside Health', 'Pinecrest Hospital', 'Oakwood Medical',
            'Silverline Clinic', 'Golden Valley Hospital', 'Harborview Medical', 'Maple Leaf Hospital', 'Cedar Health',
            'Redwood Medical', 'Bluewater Hospital', 'Summit Clinic', 'Prairie Health', 'Willowbrook Hospital'
        ]
        hospitals = []
        for i, name in enumerate(hospital_names):
            hospitals.append(Hospital(name=name, location=f'Location {i+1}'))
        db.session.add_all(hospitals)
        db.session.commit()
    # Add sample medical facilities to all hospitals
    if MedicalFacility.query.count() == 0:
        facilities = ['MRI', 'CT Scan', 'X-Ray', 'ICU', 'Emergency', 'Dialysis', 'Pharmacy', 'Lab', 'Ultrasound', 'Blood Bank']
        hospitals = Hospital.query.all()
        import random
        for hosp in hospitals:
            # Assign 3-5 random facilities to each hospital
            chosen = random.sample(facilities, k=random.randint(3,5))
            for fname in chosen:
                db.session.add(MedicalFacility(name=fname, hospital_id=hosp.id))
        db.session.commit()
    # Add demo doctors to first 5 hospitals (excess/shortage logic)
    hospitals = Hospital.query.order_by(Hospital.id).all()
    if UrbanDoctor.query.count() == 0 and len(hospitals) >= 5:
        h1, h2, h3, h4, h5 = hospitals[:5]
        cardiologists = [UrbanDoctor(name=f'Dr. Cardio{i+1}', specialty='Cardiology', hospital_id=h1.id) for i in range(6)]
        orthos = [UrbanDoctor(name=f'Dr. Ortho{i+1}', specialty='Orthopedics', hospital_id=h2.id) for i in range(2)]
        neuros = [UrbanDoctor(name=f'Dr. Neuro{i+1}', specialty='Neurology', hospital_id=h3.id) for i in range(4)]
        peds = [UrbanDoctor(name=f'Dr. Ped{i+1}', specialty='Pediatrics', hospital_id=h1.id) for i in range(3)]
        pulmos = [UrbanDoctor(name=f'Dr. Pulmo{i+1}', specialty='Pulmonology', hospital_id=h4.id) for i in range(7)]
        river_cardios = [UrbanDoctor(name=f'Dr. RiverCardio{i+1}', specialty='Cardiology', hospital_id=h5.id) for i in range(1)]
        db.session.add_all(cardiologists + orthos + neuros + peds + pulmos + river_cardios)
        # Add 25 extra doctors to all 25 hospitals
        specs = ['Cardiology', 'Orthopedics', 'Neurology', 'Pediatrics', 'Pulmonology', 'General', 'Dermatology', 'Oncology', 'Radiology', 'Gastroenterology']
        extra_docs = []
        for i in range(25):
            spec = random.choice(specs)
            hosp = random.choice(hospitals)
            extra_docs.append(UrbanDoctor(name=f'Dr. Extra{i+1}', specialty=spec, hospital_id=hosp.id))
        db.session.add_all(extra_docs)
        db.session.commit()
    if DiseaseOccurrence.query.count() == 0:
        db.session.add_all([
            DiseaseOccurrence(disease_name='Flu', count=120, city='Metropolis'),
            DiseaseOccurrence(disease_name='Diabetes', count=80, city='Metropolis'),
            DiseaseOccurrence(disease_name='Hypertension', count=95, city='Metropolis'),
            DiseaseOccurrence(disease_name='COVID-19', count=60, city='Metropolis'),
            DiseaseOccurrence(disease_name='Asthma', count=40, city='Metropolis'),
            DiseaseOccurrence(disease_name='Malaria', count=30, city='Metropolis'),
        ])
        db.session.commit()

def update_disease_stats(disease_name, city='Metropolis'):
    """Increment disease occurrence when a new case is reported."""
    disease = DiseaseOccurrence.query.filter_by(disease_name=disease_name, city=city).first()
    if disease:
        disease.count += 1
    else:
        disease = DiseaseOccurrence(disease_name=disease_name, count=1, city=city)
        db.session.add(disease)
    db.session.commit()
