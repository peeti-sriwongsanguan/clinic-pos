CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    address TEXT,
    created_at TIMESTAMP NOT NULL,
    medical_history TEXT,
    notes TEXT,
    birth_date TIMESTAMP,
    gender TEXT,
    emergency_contact TEXT
);

CREATE TABLE IF NOT EXISTS services (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    duration INTEGER NOT NULL,  -- in minutes
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    total_amount REAL NOT NULL,
    payment_method TEXT NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    status TEXT NOT NULL,  -- pending, completed, cancelled
    notes TEXT,
    discount_amount REAL DEFAULT 0,
    tax_amount REAL DEFAULT 0,
    created_by TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

CREATE TABLE IF NOT EXISTS transaction_items (
    id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    discount REAL DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

CREATE TABLE IF NOT EXISTS appointments (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status TEXT NOT NULL,  -- scheduled, completed, cancelled, no-show
    notes TEXT,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

CREATE TABLE IF NOT EXISTS staff (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    role TEXT NOT NULL,  -- admin, doctor, therapist, receptionist
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP NOT NULL
);

-- Staff commission rates
CREATE TABLE IF NOT EXISTS commission_rates (
    id TEXT PRIMARY KEY,
    staff_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    commission_percentage REAL NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP NOT NULL,
    FOREIGN KEY (staff_id) REFERENCES staff(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

-- Doctor fees
CREATE TABLE IF NOT EXISTS doctor_fees (
    id TEXT PRIMARY KEY,
    doctor_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    hourly_rate REAL NOT NULL,
    minimum_hours REAL DEFAULT 1,
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP NOT NULL,
    FOREIGN KEY (doctor_id) REFERENCES staff(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

-- Staff service assignments
CREATE TABLE IF NOT EXISTS staff_services (
    id TEXT PRIMARY KEY,
    staff_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    can_perform BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP NOT NULL,
    FOREIGN KEY (staff_id) REFERENCES staff(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

-- Language settings
CREATE TABLE IF NOT EXISTS supported_languages (
    code TEXT PRIMARY KEY,     -- e.g., 'en', 'th'
    name TEXT NOT NULL,        -- e.g., 'English', 'Thai'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL
);

-- Translations for static content
CREATE TABLE IF NOT EXISTS translations (
    id TEXT PRIMARY KEY,
    language_code TEXT NOT NULL,
    key TEXT NOT NULL,         -- translation key
    value TEXT NOT NULL,       -- translated text
    context TEXT,             -- where this translation is used
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP NOT NULL,
    FOREIGN KEY (language_code) REFERENCES supported_languages(code)
);

-- Treatment notes and medical records
CREATE TABLE IF NOT EXISTS treatment_records (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    doctor_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    treatment_date TIMESTAMP NOT NULL,
    chief_complaint TEXT,          -- Patient's main concern
    diagnosis TEXT,                -- Doctor's diagnosis
    treatment_plan TEXT,           -- Planned treatment
    treatment_notes TEXT,          -- Detailed treatment notes
    next_appointment_notes TEXT,   -- Notes for next appointment
    before_photos TEXT,            -- Comma-separated photo URLs
    after_photos TEXT,             -- Comma-separated photo URLs
    followup_required BOOLEAN DEFAULT false,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES staff(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

-- Patient progress tracking
CREATE TABLE IF NOT EXISTS treatment_progress (
    id TEXT PRIMARY KEY,
    treatment_record_id TEXT NOT NULL,
    progress_date TIMESTAMP NOT NULL,
    progress_notes TEXT,           -- Progress since last treatment
    complications TEXT,            -- Any complications
    patient_feedback TEXT,         -- Patient's feedback
    doctor_notes TEXT,             -- Doctor's notes on progress
    photos TEXT,                   -- Comma-separated photo URLs
    satisfaction_level INTEGER,    -- 1-5 scale
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP NOT NULL,
    FOREIGN KEY (treatment_record_id) REFERENCES treatment_records(id)
);

-- Custom treatment templates
CREATE TABLE IF NOT EXISTS treatment_templates (
    id TEXT PRIMARY KEY,
    service_id TEXT NOT NULL,
    name TEXT NOT NULL,
    template_content TEXT NOT NULL,    -- JSON structure for the template
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP NOT NULL,
    FOREIGN KEY (service_id) REFERENCES services(id)
);

-- Patient documents and consent forms
CREATE TABLE IF NOT EXISTS patient_documents (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    document_type TEXT NOT NULL,    -- consent_form, medical_history, etc.
    document_url TEXT NOT NULL,
    language_code TEXT NOT NULL,
    signed_by TEXT,                -- If it's a signed document
    signed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (language_code) REFERENCES supported_languages(code)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name);
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);
CREATE INDEX IF NOT EXISTS idx_services_category ON services(category);
CREATE INDEX IF NOT EXISTS idx_transactions_patient ON transactions(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(start_time);
CREATE INDEX IF NOT EXISTS idx_commission_staff ON commission_rates(staff_id);
CREATE INDEX IF NOT EXISTS idx_commission_service ON commission_rates(service_id);
CREATE INDEX IF NOT EXISTS idx_doctor_fees_doctor ON doctor_fees(doctor_id);
CREATE INDEX IF NOT EXISTS idx_doctor_fees_service ON doctor_fees(service_id);
CREATE INDEX IF NOT EXISTS idx_staff_services_staff ON staff_services(staff_id);
CREATE INDEX IF NOT EXISTS idx_staff_services_service ON staff_services(service_id);
CREATE INDEX IF NOT EXISTS idx_treatment_records_patient ON treatment_records(patient_id);
CREATE INDEX IF NOT EXISTS idx_treatment_records_doctor ON treatment_records(doctor_id);
CREATE INDEX IF NOT EXISTS idx_treatment_progress_record ON treatment_progress(treatment_record_id);
CREATE INDEX IF NOT EXISTS idx_translations_lang_key ON translations(language_code, key);