-- CarePlus Medical Assistant - Database Schema and Seed Data

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE NOT NULL,
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    emergency_contact_name VARCHAR(200),
    emergency_contact_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Health profiles table
CREATE TABLE IF NOT EXISTS health_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    allergies JSONB DEFAULT '[]',
    chronic_conditions JSONB DEFAULT '[]',
    past_procedures JSONB DEFAULT '[]',
    family_history JSONB DEFAULT '[]',
    blood_type VARCHAR(10),
    height_cm NUMERIC(5,1),
    weight_kg NUMERIC(5,1),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    appointment_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled',
    scheduled_at TIMESTAMP NOT NULL,
    location VARCHAR(255),
    provider_name VARCHAR(200),
    notes TEXT,
    cancellation_policy VARCHAR(255) DEFAULT '24 hours before appointment',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Medications table
CREATE TABLE IF NOT EXISTS medications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    instructions TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    adherence_log JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Prescriptions table
CREATE TABLE IF NOT EXISTS prescriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    medication_id INTEGER REFERENCES medications(id) ON DELETE CASCADE,
    prescribing_doctor VARCHAR(200) NOT NULL,
    refills_remaining INTEGER DEFAULT 0,
    expiry_date DATE NOT NULL,
    pharmacy VARCHAR(200),
    last_refill_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Blood results table
CREATE TABLE IF NOT EXISTS blood_results (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    test_type VARCHAR(100) NOT NULL,
    value NUMERIC(10,2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    reference_range_low NUMERIC(10,2),
    reference_range_high NUMERIC(10,2),
    tested_at TIMESTAMP NOT NULL,
    lab_name VARCHAR(200),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Consultation requests table
CREATE TABLE IF NOT EXISTS consultation_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    consultation_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    reason TEXT,
    documents JSONB DEFAULT '[]',
    assigned_physician VARCHAR(200),
    scheduled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SEED DATA
-- ============================================================

-- Demo user
INSERT INTO users (id, first_name, last_name, email, phone, date_of_birth, address_line1, city, state, zip_code, emergency_contact_name, emergency_contact_phone)
VALUES (1, 'Sarah', 'Johnson', 'sarah.johnson@email.com', '+1-555-0142', '1985-03-15', '742 Evergreen Terrace', 'Springfield', 'Illinois', '62701', 'Michael Johnson', '+1-555-0198');

-- Health profile
INSERT INTO health_profiles (user_id, allergies, chronic_conditions, past_procedures, family_history, blood_type, height_cm, weight_kg)
VALUES (1,
    '["Penicillin", "Shellfish"]',
    '["Hypertension", "Mild Asthma"]',
    '[{"name": "Appendectomy", "year": 2019, "hospital": "Springfield General"}, {"name": "Wisdom teeth removal", "year": 2010, "hospital": "Dental Surgery Center"}]',
    '[{"condition": "Type 2 Diabetes", "relation": "Father"}, {"condition": "Breast Cancer", "relation": "Maternal Grandmother"}, {"condition": "Hypertension", "relation": "Mother"}]',
    'A+', 165.0, 62.5
);

-- Upcoming appointments
INSERT INTO appointments (user_id, appointment_type, status, scheduled_at, location, provider_name, notes) VALUES
(1, 'General Checkup', 'scheduled', NOW() + INTERVAL '7 days', 'Springfield Medical Center, Room 204', 'Dr. Emily Carter', 'Annual physical examination'),
(1, 'Dental Cleaning', 'scheduled', NOW() + INTERVAL '14 days', 'Bright Smile Dental, Suite 101', 'Dr. Robert Chen', 'Routine cleaning and checkup'),
(1, 'Cardiology Follow-up', 'scheduled', NOW() + INTERVAL '21 days', 'Heart Health Clinic, Floor 3', 'Dr. Amanda Torres', 'Blood pressure monitoring follow-up');

-- Medications
INSERT INTO medications (user_id, name, dosage, frequency, start_date, end_date, instructions, is_active, adherence_log) VALUES
(1, 'Lisinopril', '10mg', 'Once daily', '2023-01-15', NULL, 'Take in the morning with water', TRUE, '[{"date": "2026-06-20", "taken": true}, {"date": "2026-06-21", "taken": true}, {"date": "2026-06-22", "taken": false}]'),
(1, 'Albuterol Inhaler', '90mcg', 'As needed', '2022-06-01', NULL, 'Use for asthma symptoms, max 2 puffs every 4 hours', TRUE, '[]'),
(1, 'Vitamin D3', '2000 IU', 'Once daily', '2024-03-01', NULL, 'Take with food', TRUE, '[{"date": "2026-06-20", "taken": true}, {"date": "2026-06-21", "taken": true}, {"date": "2026-06-22", "taken": true}]'),
(1, 'Atorvastatin', '20mg', 'Once daily at bedtime', '2024-09-01', NULL, 'Take at bedtime', TRUE, '[{"date": "2026-06-20", "taken": true}, {"date": "2026-06-21", "taken": false}, {"date": "2026-06-22", "taken": true}]'),
(1, 'Amoxicillin', '500mg', 'Three times daily', '2026-06-10', '2026-06-24', 'Complete full course. Take with food.', TRUE, '[]');

-- Prescriptions
INSERT INTO prescriptions (user_id, medication_id, prescribing_doctor, refills_remaining, expiry_date, pharmacy, last_refill_date) VALUES
(1, 1, 'Dr. Amanda Torres', 3, '2027-01-15', 'CVS Pharmacy - Main St', '2026-05-15'),
(1, 2, 'Dr. Emily Carter', 5, '2027-06-01', 'CVS Pharmacy - Main St', '2026-03-01'),
(1, 3, 'Dr. Emily Carter', 6, '2027-03-01', 'Walgreens - Oak Ave', '2026-04-01'),
(1, 4, 'Dr. Amanda Torres', 2, '2026-09-01', 'CVS Pharmacy - Main St', '2026-06-01'),
(1, 5, 'Dr. Emily Carter', 0, '2026-06-24', 'CVS Pharmacy - Main St', NULL);

-- Blood results (12 months of history)
INSERT INTO blood_results (user_id, test_type, value, unit, reference_range_low, reference_range_high, tested_at, lab_name) VALUES
-- Total Cholesterol
(1, 'Total Cholesterol', 245.00, 'mg/dL', 125.00, 200.00, '2025-07-15 09:00:00', 'Quest Diagnostics'),
(1, 'Total Cholesterol', 232.00, 'mg/dL', 125.00, 200.00, '2025-10-15 09:00:00', 'Quest Diagnostics'),
(1, 'Total Cholesterol', 218.00, 'mg/dL', 125.00, 200.00, '2026-01-15 09:00:00', 'Quest Diagnostics'),
(1, 'Total Cholesterol', 205.00, 'mg/dL', 125.00, 200.00, '2026-04-15 09:00:00', 'Quest Diagnostics'),
(1, 'Total Cholesterol', 198.00, 'mg/dL', 125.00, 200.00, '2026-06-15 09:00:00', 'Quest Diagnostics'),
-- LDL Cholesterol
(1, 'LDL Cholesterol', 165.00, 'mg/dL', 0.00, 100.00, '2025-07-15 09:00:00', 'Quest Diagnostics'),
(1, 'LDL Cholesterol', 152.00, 'mg/dL', 0.00, 100.00, '2025-10-15 09:00:00', 'Quest Diagnostics'),
(1, 'LDL Cholesterol', 138.00, 'mg/dL', 0.00, 100.00, '2026-01-15 09:00:00', 'Quest Diagnostics'),
(1, 'LDL Cholesterol', 125.00, 'mg/dL', 0.00, 100.00, '2026-04-15 09:00:00', 'Quest Diagnostics'),
(1, 'LDL Cholesterol', 118.00, 'mg/dL', 0.00, 100.00, '2026-06-15 09:00:00', 'Quest Diagnostics'),
-- Fasting Blood Sugar
(1, 'Fasting Blood Sugar', 110.00, 'mg/dL', 70.00, 100.00, '2025-07-15 09:00:00', 'Quest Diagnostics'),
(1, 'Fasting Blood Sugar', 105.00, 'mg/dL', 70.00, 100.00, '2025-10-15 09:00:00', 'Quest Diagnostics'),
(1, 'Fasting Blood Sugar', 102.00, 'mg/dL', 70.00, 100.00, '2026-01-15 09:00:00', 'Quest Diagnostics'),
(1, 'Fasting Blood Sugar', 98.00, 'mg/dL', 70.00, 100.00, '2026-04-15 09:00:00', 'Quest Diagnostics'),
(1, 'Fasting Blood Sugar', 95.00, 'mg/dL', 70.00, 100.00, '2026-06-15 09:00:00', 'Quest Diagnostics'),
-- Hemoglobin
(1, 'Hemoglobin', 13.5, 'g/dL', 12.0, 16.0, '2025-07-15 09:00:00', 'Quest Diagnostics'),
(1, 'Hemoglobin', 13.8, 'g/dL', 12.0, 16.0, '2025-10-15 09:00:00', 'Quest Diagnostics'),
(1, 'Hemoglobin', 14.0, 'g/dL', 12.0, 16.0, '2026-01-15 09:00:00', 'Quest Diagnostics'),
(1, 'Hemoglobin', 13.9, 'g/dL', 12.0, 16.0, '2026-04-15 09:00:00', 'Quest Diagnostics'),
(1, 'Hemoglobin', 14.1, 'g/dL', 12.0, 16.0, '2026-06-15 09:00:00', 'Quest Diagnostics'),
-- HbA1c
(1, 'HbA1c', 6.2, '%', 4.0, 5.7, '2025-07-15 09:00:00', 'Quest Diagnostics'),
(1, 'HbA1c', 6.0, '%', 4.0, 5.7, '2025-10-15 09:00:00', 'Quest Diagnostics'),
(1, 'HbA1c', 5.9, '%', 4.0, 5.7, '2026-01-15 09:00:00', 'Quest Diagnostics'),
(1, 'HbA1c', 5.8, '%', 4.0, 5.7, '2026-04-15 09:00:00', 'Quest Diagnostics'),
(1, 'HbA1c', 5.7, '%', 4.0, 5.7, '2026-06-15 09:00:00', 'Quest Diagnostics');

-- Reset sequence for users table
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
