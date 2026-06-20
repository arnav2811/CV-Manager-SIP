-- ============================================================
-- CV Manager — Education Seed Data
-- Generated for: Growth Grids × University of Southampton Delhi
-- SIP Project — Qualification Standardization
-- ============================================================
--
-- This file creates the 5-table education schema and seeds it
-- with canonical reference data. Load this into MySQL/MariaDB
-- to bootstrap the qualification normalization system.
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- Table 1: qualification_levels (education hierarchy)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS qualification_levels (
  level_id    INT PRIMARY KEY AUTO_INCREMENT,
  level_name  VARCHAR(100) NOT NULL,
  level_rank  INT NOT NULL
);

INSERT INTO qualification_levels (level_name, level_rank) VALUES
  ('SCHOOL', 1),
  ('DIPLOMA', 2),
  ('UG ENGINEERING', 3),
  ('UG SCIENCE', 3),
  ('PG ENGINEERING', 4),
  ('PG OTHER', 4),
  ('DOCTORATE', 5);

-- ────────────────────────────────────────────────────────────
-- Table 2: qualification_canonical (19 canonical degree types)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS qualification_canonical (
  canonical_id    INT PRIMARY KEY AUTO_INCREMENT,
  canonical_name  VARCHAR(255) NOT NULL,
  level_id        INT NOT NULL,
  short_code      VARCHAR(20) NOT NULL,
  FOREIGN KEY (level_id) REFERENCES qualification_levels(level_id)
);

INSERT INTO qualification_canonical (canonical_name, level_id, short_code) VALUES
  -- UG Engineering (level_id = 3, maps to 'UG ENGINEERING')
  ('Bachelor of Technology', 3, 'BTECH'),
  ('Bachelor of Engineering', 3, 'BE'),
  -- UG Science (level_id = 4, maps to 'UG SCIENCE')
  ('Bachelor of Science', 4, 'BSC'),
  ('Bachelor of Computer Applications', 4, 'BCA'),
  ('Bachelor of Commerce', 4, 'BCOM'),
  ('Bachelor of Business Administration', 4, 'BBA'),
  ('Bachelor of Arts', 4, 'BA'),
  -- PG Engineering (level_id = 5, maps to 'PG ENGINEERING')
  ('Master of Technology', 5, 'MTECH'),
  ('Master of Engineering', 5, 'ME'),
  -- PG Other (level_id = 6, maps to 'PG OTHER')
  ('Master of Science', 6, 'MSC'),
  ('Master of Computer Applications', 6, 'MCA'),
  ('Master of Business Administration', 6, 'MBA'),
  ('Master of Commerce', 6, 'MCOM'),
  ('Master of Arts', 6, 'MA'),
  -- Doctorate (level_id = 7, maps to 'DOCTORATE')
  ('Doctor of Philosophy', 7, 'PHD'),
  -- Diploma (level_id = 2, maps to 'DIPLOMA')
  ('Diploma in Engineering', 2, 'DIPENG'),
  ('Post Graduate Diploma', 2, 'PGD'),
  -- School (level_id = 1, maps to 'SCHOOL')
  ('12th Standard', 1, '12TH'),
  ('10th Standard', 1, '10TH');

-- ────────────────────────────────────────────────────────────
-- Table 3: qualification_aliases (sample aliases — full set
-- is in degree_aliases.csv for bulk import)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS qualification_aliases (
  alias_id      INT PRIMARY KEY AUTO_INCREMENT,
  raw_string    VARCHAR(255) NOT NULL,
  canonical_id  INT NOT NULL,
  normalized    VARCHAR(255) NOT NULL,
  source        VARCHAR(50) DEFAULT 'manual',
  confidence    FLOAT DEFAULT 1.0,
  INDEX idx_normalized (normalized),
  FOREIGN KEY (canonical_id) REFERENCES qualification_canonical(canonical_id)
);

-- Sample aliases (representative subset; full 6,980+ set is in degree_aliases.csv)
INSERT INTO qualification_aliases (raw_string, canonical_id, normalized, source, confidence) VALUES
  -- Bachelor of Technology aliases (canonical_id = 1)
  ('B.Tech', 1, 'btech', 'manual', 1.0),
  ('BTech', 1, 'btech', 'manual', 1.0),
  ('B. Tech', 1, 'b tech', 'manual', 1.0),
  ('BTECH', 1, 'btech', 'manual', 1.0),
  ('B.Tech (Hons)', 1, 'btech', 'manual', 1.0),
  ('Bachelor of Technology', 1, 'bachelor of technology', 'manual', 1.0),
  -- Bachelor of Engineering aliases (canonical_id = 2)
  ('B.E.', 2, 'be', 'manual', 1.0),
  ('BE', 2, 'be', 'manual', 1.0),
  ('BEng', 2, 'beng', 'manual', 1.0),
  ('Bachelor of Engineering', 2, 'bachelor of engineering', 'manual', 1.0),
  -- Bachelor of Science aliases (canonical_id = 3)
  ('B.Sc', 3, 'bsc', 'manual', 1.0),
  ('BSc', 3, 'bsc', 'manual', 1.0),
  ('Bachelor of Science', 3, 'bachelor of science', 'manual', 1.0),
  -- MBA aliases (canonical_id = 12)
  ('MBA', 12, 'mba', 'manual', 1.0),
  ('M.B.A.', 12, 'mba', 'manual', 1.0),
  ('EMBA', 12, 'emba', 'manual', 1.0),
  -- Post Graduate Diploma aliases (canonical_id = 17)
  ('PGDM', 17, 'pgdm', 'manual', 1.0),
  ('PGD', 17, 'pgd', 'manual', 1.0),
  ('PGDBA', 17, 'pgdba', 'manual', 1.0),
  ('PG Diploma', 17, 'pg diploma', 'manual', 1.0),
  -- PhD aliases (canonical_id = 15)
  ('PhD', 15, 'phd', 'manual', 1.0),
  ('Ph.D', 15, 'phd', 'manual', 1.0),
  ('DPhil', 15, 'dphil', 'manual', 1.0),
  -- School aliases
  ('HSC', 18, 'hsc', 'manual', 1.0),
  ('10+2', 18, '10+2', 'manual', 1.0),
  ('SSC', 19, 'ssc', 'manual', 1.0),
  ('Matric', 19, 'matric', 'manual', 1.0);

-- ────────────────────────────────────────────────────────────
-- Table 4: field_of_study (68 canonical fields)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS field_of_study (
  field_id        INT PRIMARY KEY AUTO_INCREMENT,
  canonical_field VARCHAR(255) NOT NULL,
  category        VARCHAR(100) NOT NULL,
  field_aliases   TEXT
);

INSERT INTO field_of_study (canonical_field, category, field_aliases) VALUES
  -- Engineering & Technology (20 fields)
  ('Computer Science and Engineering', 'ENGINEERING & TECHNOLOGY', '["CSE","C.S.E","CS","Computer Science","Comp Science","CompSci"]'),
  ('Information Technology', 'ENGINEERING & TECHNOLOGY', '["IT","I.T","Info Tech","Infotech","Information Science"]'),
  ('Electronics and Communication Engineering', 'ENGINEERING & TECHNOLOGY', '["ECE","E.C.E","E&C","Electronics & Communication"]'),
  ('Electrical Engineering', 'ENGINEERING & TECHNOLOGY', '["EE","E.E","EEE","Electrical","Electrical & Electronics"]'),
  ('Mechanical Engineering', 'ENGINEERING & TECHNOLOGY', '["ME","M.E","Mech","Mech Engg","Mechanical Engg"]'),
  ('Civil Engineering', 'ENGINEERING & TECHNOLOGY', '["CE","C.E","Civil","Civil Engg"]'),
  ('Chemical Engineering', 'ENGINEERING & TECHNOLOGY', '["ChE","Chem Engg","Chemical Engg"]'),
  ('Aerospace Engineering', 'ENGINEERING & TECHNOLOGY', '["Aero","Aerospace","Aeronautical","Aero Engg"]'),
  ('Biotechnology Engineering', 'ENGINEERING & TECHNOLOGY', '["Biotech","Biotechnology","Bio Tech","Biotech Engg"]'),
  ('Artificial Intelligence and Machine Learning', 'ENGINEERING & TECHNOLOGY', '["AI","ML","AI & ML","AI/ML","AIML"]'),
  ('Data Science', 'ENGINEERING & TECHNOLOGY', '["DS","Data Analytics","Big Data","Data Sc"]'),
  ('Cybersecurity', 'ENGINEERING & TECHNOLOGY', '["Cyber Security","Information Security","InfoSec"]'),
  ('Software Engineering', 'ENGINEERING & TECHNOLOGY', '["SE","S.E","Software","SWE","Software Engg"]'),
  ('Instrumentation Engineering', 'ENGINEERING & TECHNOLOGY', '["IE","I&C","Instrumentation","Instrumentation Engg"]'),
  ('Production Engineering', 'ENGINEERING & TECHNOLOGY', '["Production","Manufacturing","Industrial Engineering"]'),
  ('Mining Engineering', 'ENGINEERING & TECHNOLOGY', '["Mining","Mining Engg"]'),
  ('Metallurgical Engineering', 'ENGINEERING & TECHNOLOGY', '["Metallurgy","Materials Science","Materials Engg"]'),
  ('Environmental Engineering', 'ENGINEERING & TECHNOLOGY', '["Env Engg","Environmental Engg","Environment Engineering"]'),
  ('Textile Engineering', 'ENGINEERING & TECHNOLOGY', '["Textile","Textile Engg","Textiles","Textile Technology"]'),
  ('Food Technology', 'ENGINEERING & TECHNOLOGY', '["Food Tech","Food Science","Food Science & Technology"]'),
  -- Pure Sciences (12 fields)
  ('Physics', 'PURE SCIENCES', '["Phy","Applied Physics","Engineering Physics"]'),
  ('Chemistry', 'PURE SCIENCES', '["Chem","Applied Chemistry","Industrial Chemistry"]'),
  ('Mathematics', 'PURE SCIENCES', '["Maths","Math","Applied Mathematics","Pure Mathematics"]'),
  ('Statistics', 'PURE SCIENCES', '["Stats","Applied Statistics","Statistics & Data Science"]'),
  ('Biology', 'PURE SCIENCES', '["Bio","Life Sciences","Biological Sciences"]'),
  ('Microbiology', 'PURE SCIENCES', '["Micro Bio","Micro Biology"]'),
  ('Biochemistry', 'PURE SCIENCES', '["Bio Chemistry","Biochem"]'),
  ('Bioinformatics', 'PURE SCIENCES', '["Bio Informatics","Computational Biology"]'),
  ('Zoology', 'PURE SCIENCES', '["Zoo"]'),
  ('Botany', 'PURE SCIENCES', '["Plant Science"]'),
  ('Geology', 'PURE SCIENCES', '["Earth Science"]'),
  ('Environmental Science', 'PURE SCIENCES', '["Env Science","Environmental Studies"]'),
  -- Computer Applications (2 fields)
  ('Computer Applications', 'COMPUTER APPLICATIONS', '["Comp Applications","CA","Computer Application"]'),
  ('Computer Science (Applications)', 'COMPUTER APPLICATIONS', '["CS Applications","Computer Science Applications"]'),
  -- Management & Commerce (10 fields)
  ('Business Administration', 'MANAGEMENT & COMMERCE', '["Business Admin","Business Mgmt","Business Management","Management"]'),
  ('Finance', 'MANAGEMENT & COMMERCE', '["Financial Management","Finance & Accounts","Corporate Finance"]'),
  ('Marketing', 'MANAGEMENT & COMMERCE', '["Marketing Management","Sales & Marketing","Digital Marketing"]'),
  ('Human Resources Management', 'MANAGEMENT & COMMERCE', '["HR","HRM","Human Resources","People Management"]'),
  ('Operations Management', 'MANAGEMENT & COMMERCE', '["Operations","Supply Chain","Supply Chain Management","Logistics"]'),
  ('International Business', 'MANAGEMENT & COMMERCE', '["IB","International Trade","Global Business"]'),
  ('Entrepreneurship', 'MANAGEMENT & COMMERCE', '["Startup Management","Entrepreneurship & Innovation"]'),
  ('Commerce', 'MANAGEMENT & COMMERCE', '["Business Studies"]'),
  ('Accounting', 'MANAGEMENT & COMMERCE', '["Accountancy","Accounts","Financial Accounting","Cost Accounting"]'),
  ('Banking and Finance', 'MANAGEMENT & COMMERCE', '["Banking & Finance","Banking","Finance & Banking"]'),
  -- Humanities & Social Sciences (11 fields)
  ('Economics', 'HUMANITIES & SOCIAL SCIENCES', '["Eco","Applied Economics","Business Economics"]'),
  ('Psychology', 'HUMANITIES & SOCIAL SCIENCES', '["Psych","Applied Psychology","Industrial Psychology"]'),
  ('Sociology', 'HUMANITIES & SOCIAL SCIENCES', '["Social Work"]'),
  ('Political Science', 'HUMANITIES & SOCIAL SCIENCES', '["Pol Science","Politics"]'),
  ('History', 'HUMANITIES & SOCIAL SCIENCES', '[]'),
  ('Geography', 'HUMANITIES & SOCIAL SCIENCES', '["Geo"]'),
  ('English', 'HUMANITIES & SOCIAL SCIENCES', '["English Literature","English Lang & Lit","English Language"]'),
  ('Hindi', 'HUMANITIES & SOCIAL SCIENCES', '["Hindi Literature"]'),
  ('Philosophy', 'HUMANITIES & SOCIAL SCIENCES', '["Phil"]'),
  ('Public Administration', 'HUMANITIES & SOCIAL SCIENCES', '["Public Admin","Pub Admin"]'),
  ('Mass Communication', 'HUMANITIES & SOCIAL SCIENCES', '["Mass Comm","Journalism","JMC","Media Studies","Media & Communication"]'),
  -- Law (1 field)
  ('Law', 'LAW', '["LLB","Legal Studies","Jurisprudence","Corporate Law","Criminal Law"]'),
  -- Medicine & Health (6 fields)
  ('Medicine', 'MEDICINE & HEALTH', '["MBBS","Medical"]'),
  ('Nursing', 'MEDICINE & HEALTH', '["BSc Nursing"]'),
  ('Pharmacy', 'MEDICINE & HEALTH', '["Pharmaceutical Sciences","Pharma"]'),
  ('Physiotherapy', 'MEDICINE & HEALTH', '["Physical Therapy","BPT"]'),
  ('Dentistry', 'MEDICINE & HEALTH', '["BDS","Dental"]'),
  ('Ayurveda', 'MEDICINE & HEALTH', '["BAMS","Ayurvedic Medicine"]'),
  -- Architecture & Design (2 fields)
  ('Architecture', 'ARCHITECTURE & DESIGN', '["Arch","B.Arch","Urban Design"]'),
  ('Design', 'ARCHITECTURE & DESIGN', '["Industrial Design","Product Design","Fashion Design","Interior Design","Graphic Design","UX Design","UI/UX"]'),
  -- Education, Hospitality, Agriculture, General (4 fields)
  ('Education', 'EDUCATION', '["B.Ed","Teaching","Teacher Education"]'),
  ('Hotel Management', 'HOSPITALITY', '["Hospitality","Hospitality Management","Tourism & Hospitality","BHMCT"]'),
  ('Agriculture', 'AGRICULTURE', '["Agricultural Science","Agri","Horticulture"]'),
  ('General', 'GENERAL', '["Not Specified","NA","N/A"]');

-- ────────────────────────────────────────────────────────────
-- Table 5: candidate_education (sample records)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS candidate_education (
  edu_id          INT PRIMARY KEY AUTO_INCREMENT,
  candidate_id    INT NOT NULL,
  raw_degree      VARCHAR(255),
  raw_field       VARCHAR(255),
  canonical_id    INT,
  field_id        INT,
  institution     VARCHAR(255),
  graduation_year INT,
  cgpa            FLOAT,
  parse_status    ENUM('resolved', 'fuzzy_matched', 'review_needed', 'unresolved') DEFAULT 'unresolved',
  confidence      FLOAT DEFAULT 0.0,
  FOREIGN KEY (canonical_id) REFERENCES qualification_canonical(canonical_id),
  FOREIGN KEY (field_id) REFERENCES field_of_study(field_id)
);

INSERT INTO candidate_education (candidate_id, raw_degree, raw_field, canonical_id, field_id, institution, graduation_year, cgpa, parse_status, confidence) VALUES
  (1, 'B.Tech', 'CSE', 1, 1, 'IIT Delhi', 2022, 8.5, 'resolved', 1.0),
  (2, 'Bacheler of Technology', 'Mech', 1, 5, 'VIT', 2021, 8.0, 'fuzzy_matched', 0.91),
  (3, 'Kuch bhi', 'idk', NULL, NULL, 'Unknown', 2020, 7.0, 'unresolved', 0.0);

-- ============================================================
-- NOTE: The full alias dataset (6,980+ entries) is provided in
-- degree_aliases.csv for bulk import. Use LOAD DATA INFILE or
-- equivalent to import the complete alias dictionary.
--
-- The full field alias dataset (308 entries) is provided in
-- field_of_study_aliases.csv.
--
-- See also: education_reference_seed.sql for the field alias
-- and degree-field mapping tables.
-- ============================================================
