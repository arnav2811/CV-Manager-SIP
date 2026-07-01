"""
Field of Study / Major Lookup Table
====================================
Builds a comprehensive subject/discipline reference table for Indian degrees.
Covers all UGC/AICTE-recognized disciplines + aliases for how candidates
write their specialization on resumes.

Structure:
  field_of_study table  → canonical subject names + aliases
  degree_field_map      → which degree types are valid for which fields
  full_education_ref    → combined (degree_type × field_of_study) reference
"""

import csv, json, itertools, os

# ─────────────────────────────────────────────────────────────────
# 1. FIELDS OF STUDY  (canonical → list of aliases)
# ─────────────────────────────────────────────────────────────────
# Organized by broad category (matches UGC discipline groups)

FIELDS = {

    # ── ENGINEERING & TECHNOLOGY ─────────────────────────────────
    "Computer Science and Engineering": [
        "CSE", "C.S.E", "C.S.E.", "CS", "Computer Science", "Comp Science",
        "Computer Sc", "Computer Sc.", "Computer Sc. & Engg", "CS&E",
        "Computer Science & Engineering", "Computers", "CompSci",
        "Information Technology", "IT",  # often used interchangeably at UG
    ],
    "Information Technology": [
        "IT", "I.T", "I.T.", "Info Tech", "Infotech",
        "Information Tech", "Information Technology",
        "Information Science", "IS", "I.S.",
    ],
    "Electronics and Communication Engineering": [
        "ECE", "E.C.E", "Electronics & Communication",
        "Electronics and Communication", "E&C", "EC",
        "Electronics Communication", "Elec & Comm",
    ],
    "Electrical Engineering": [
        "EE", "E.E", "Electrical", "Elect Engg",
        "Electrical & Electronics", "EEE", "E.E.E",
        "Electrical Electronics", "Electrical Engg",
    ],
    "Mechanical Engineering": [
        "ME", "M.E", "Mechanical", "Mech", "Mech Engg",
        "Mechanical Engg", "Mech. Engg", "Mechanical Engineering",
    ],
    "Civil Engineering": [
        "CE", "C.E", "Civil", "Civil Engg", "Civil Engg.",
        "Civil Engineering",
    ],
    "Chemical Engineering": [
        "Chem Engg", "Chemical Engg", "Chemical", "ChE",
        "Chemical Engineering",
    ],
    "Aerospace Engineering": [
        "Aero", "Aerospace", "Aeronautical", "Aero Engg",
        "Aeronautical Engineering", "Aerospace Engg",
    ],
    "Biotechnology Engineering": [
        "Biotech", "Biotechnology", "Bio Tech", "Bio Technology",
        "Biotechnology Engg", "Biotech Engg",
    ],
    "Artificial Intelligence and Machine Learning": [
        "AI", "ML", "AI & ML", "AI/ML", "Artificial Intelligence",
        "Machine Learning", "AI and ML", "AIML",
        "Artificial Intelligence & Machine Learning",
    ],
    "Data Science": [
        "Data Science", "DS", "Data Analytics", "Big Data",
        "Data Science & Analytics", "Data Sc",
    ],
    "Cybersecurity": [
        "Cybersecurity", "Cyber Security", "Information Security",
        "Network Security", "InfoSec",
    ],
    "Software Engineering": [
        "Software Engg", "Software Engineering", "SE", "S.E",
        "Software", "SWE",
    ],
    "Instrumentation Engineering": [
        "Instrumentation", "Instrumentation Engg", "IE", "I&C",
        "Instrumentation and Control",
    ],
    "Production Engineering": [
        "Production", "Production Engg", "Manufacturing",
        "Manufacturing Engg", "Industrial Engineering", "IE",
    ],
    "Mining Engineering": [
        "Mining", "Mining Engg", "Mining Engineering",
    ],
    "Metallurgical Engineering": [
        "Metallurgy", "Metallurgical Engg", "Materials Science",
        "Materials Engg", "Metallurgy & Material Science",
    ],
    "Environmental Engineering": [
        "Environmental Engg", "Environmental Engineering",
        "Environment Engineering", "Env Engg",
    ],
    "Textile Engineering": [
        "Textile", "Textile Engg", "Textiles", "Textile Technology",
    ],
    "Food Technology": [
        "Food Tech", "Food Technology", "Food Science",
        "Food Science & Technology",
    ],

    # ── PURE SCIENCES ────────────────────────────────────────────
    "Physics": [
        "Physics", "Phy", "Applied Physics", "Engineering Physics",
    ],
    "Chemistry": [
        "Chemistry", "Chem", "Applied Chemistry", "Industrial Chemistry",
    ],
    "Mathematics": [
        "Mathematics", "Maths", "Math", "Applied Mathematics",
        "Pure Mathematics", "Stats & Maths",
    ],
    "Statistics": [
        "Statistics", "Stats", "Applied Statistics",
        "Statistics & Data Science",
    ],
    "Biology": [
        "Biology", "Bio", "Life Sciences", "Biological Sciences",
    ],
    "Microbiology": [
        "Microbiology", "Micro Bio", "Micro Biology",
    ],
    "Biochemistry": [
        "Biochemistry", "Bio Chemistry", "Biochem",
    ],
    "Bioinformatics": [
        "Bioinformatics", "Bio Informatics", "Computational Biology",
    ],
    "Zoology": ["Zoology", "Zoo"],
    "Botany": ["Botany", "Plant Science"],
    "Geology": ["Geology", "Earth Science"],
    "Environmental Science": [
        "Environmental Science", "Env Science", "Environmental Studies",
    ],

    # ── COMPUTER APPLICATIONS ─────────────────────────────────────
    "Computer Applications": [
        "Computer Applications", "Comp Applications", "CA",
        "Computer Application",
    ],
    "Computer Science (Applications)": [
        "Computer Science (Applications)", "CS Applications",
        "Computer Science Applications",
    ],

    # ── MANAGEMENT & COMMERCE ────────────────────────────────────
    "Business Administration": [
        "Business Administration", "Business Admin", "Business Mgmt",
        "Business Management", "Management",
    ],
    "Finance": [
        "Finance", "Financial Management", "Finance & Accounts",
        "Corporate Finance",
    ],
    "Marketing": [
        "Marketing", "Marketing Management", "Sales & Marketing",
        "Digital Marketing",
    ],
    "Human Resources Management": [
        "Human Resources", "HR", "HRM", "Human Resource Management",
        "People Management", "HR & OB",
    ],
    "Operations Management": [
        "Operations", "Operations Management", "Supply Chain",
        "Supply Chain Management", "Logistics",
    ],
    "International Business": [
        "International Business", "IB", "International Trade",
        "Global Business",
    ],
    "Entrepreneurship": [
        "Entrepreneurship", "Startup Management",
        "Entrepreneurship & Innovation",
    ],
    "Commerce": [
        "Commerce", "Business Studies",
    ],
    "Accounting": [
        "Accounting", "Accountancy", "Accounts", "Financial Accounting",
        "Cost Accounting",
    ],
    "Banking and Finance": [
        "Banking & Finance", "Banking and Finance", "Banking",
        "Finance & Banking",
    ],

    # ── HUMANITIES & SOCIAL SCIENCES ────────────────────────────
    "Economics": [
        "Economics", "Eco", "Applied Economics", "Business Economics",
    ],
    "Psychology": [
        "Psychology", "Psych", "Applied Psychology",
        "Industrial Psychology", "Organizational Behaviour",
    ],
    "Sociology": ["Sociology", "Social Work"],
    "Political Science": [
        "Political Science", "Pol Science", "Politics",
    ],
    "History": ["History"],
    "Geography": ["Geography", "Geo"],
    "English": [
        "English", "English Literature", "English Lang & Lit",
        "English Language",
    ],
    "Hindi": ["Hindi", "Hindi Literature"],
    "Philosophy": ["Philosophy", "Phil"],
    "Public Administration": [
        "Public Administration", "Public Admin", "Pub Admin",
    ],
    "Mass Communication": [
        "Mass Communication", "Mass Comm", "Journalism",
        "Journalism & Mass Communication", "JMC", "Media Studies",
        "Media & Communication",
    ],

    # ── LAW ──────────────────────────────────────────────────────
    "Law": [
        "Law", "LLB", "Legal Studies", "Jurisprudence",
        "Corporate Law", "Criminal Law",
    ],

    # ── MEDICINE & HEALTH ────────────────────────────────────────
    "Medicine": ["MBBS", "Medicine", "Medical"],
    "Nursing": ["Nursing", "BSc Nursing"],
    "Pharmacy": ["Pharmacy", "Pharmaceutical Sciences", "Pharma"],
    "Physiotherapy": ["Physiotherapy", "Physical Therapy", "BPT"],
    "Dentistry": ["Dentistry", "BDS", "Dental"],
    "Ayurveda": ["Ayurveda", "BAMS", "Ayurvedic Medicine"],

    # ── ARCHITECTURE & DESIGN ────────────────────────────────────
    "Architecture": [
        "Architecture", "Arch", "B.Arch", "Urban Design",
    ],
    "Design": [
        "Design", "Industrial Design", "Product Design",
        "Fashion Design", "Interior Design", "Graphic Design",
        "UX Design", "UI/UX",
    ],

    # ── EDUCATION ────────────────────────────────────────────────
    "Education": [
        "Education", "B.Ed", "Teaching", "Teacher Education",
    ],

    # ── HOTEL MANAGEMENT & HOSPITALITY ───────────────────────────
    "Hotel Management": [
        "Hotel Management", "Hospitality", "Hospitality Management",
        "Tourism & Hospitality", "BHMCT",
    ],

    # ── AGRICULTURE ─────────────────────────────────────────────
    "Agriculture": [
        "Agriculture", "Agricultural Science", "Agri", "Horticulture",
    ],

    # ── GENERAL / UNSPECIFIED ────────────────────────────────────
    "General": [
        "General", "Not Specified", "NA", "N/A", "-", "",
    ],
}

# ─────────────────────────────────────────────────────────────────
# 2. DEGREE ↔ FIELD MAPPING
# (which degree types are typically paired with which fields)
# ─────────────────────────────────────────────────────────────────

DEGREE_FIELD_MAP = {
    "Bachelor of Technology": [
        "Computer Science and Engineering", "Information Technology",
        "Electronics and Communication Engineering", "Electrical Engineering",
        "Mechanical Engineering", "Civil Engineering", "Chemical Engineering",
        "Aerospace Engineering", "Biotechnology Engineering",
        "Artificial Intelligence and Machine Learning", "Data Science",
        "Cybersecurity", "Software Engineering", "Instrumentation Engineering",
        "Production Engineering", "Metallurgical Engineering",
        "Environmental Engineering", "Textile Engineering", "Food Technology",
    ],
    "Bachelor of Engineering": [
        "Computer Science and Engineering", "Information Technology",
        "Electronics and Communication Engineering", "Electrical Engineering",
        "Mechanical Engineering", "Civil Engineering", "Chemical Engineering",
        "Aerospace Engineering", "Biotechnology Engineering",
        "Instrumentation Engineering", "Production Engineering",
    ],
    "Bachelor of Science": [
        "Physics", "Chemistry", "Mathematics", "Statistics", "Biology",
        "Microbiology", "Biochemistry", "Bioinformatics", "Zoology",
        "Botany", "Geology", "Environmental Science",
        "Computer Science and Engineering", "Information Technology",
        "Nursing", "Agriculture",
    ],
    "Bachelor of Computer Applications": ["Computer Applications"],
    "Bachelor of Commerce": [
        "Commerce", "Accounting", "Finance", "Banking and Finance",
    ],
    "Bachelor of Business Administration": [
        "Business Administration", "Finance", "Marketing",
        "Human Resources Management", "International Business",
        "Entrepreneurship",
    ],
    "Bachelor of Arts": [
        "Economics", "Psychology", "Sociology", "Political Science",
        "History", "Geography", "English", "Hindi", "Philosophy",
        "Public Administration", "Mass Communication",
    ],
    "Master of Technology": [
        "Computer Science and Engineering", "Information Technology",
        "Electronics and Communication Engineering", "Electrical Engineering",
        "Mechanical Engineering", "Civil Engineering", "Data Science",
        "Artificial Intelligence and Machine Learning", "Cybersecurity",
        "Software Engineering", "Biotechnology Engineering",
    ],
    "Master of Engineering": [
        "Computer Science and Engineering", "Electronics and Communication Engineering",
        "Electrical Engineering", "Mechanical Engineering", "Civil Engineering",
    ],
    "Master of Science": [
        "Physics", "Chemistry", "Mathematics", "Statistics", "Biology",
        "Microbiology", "Biochemistry", "Bioinformatics",
        "Computer Science and Engineering", "Data Science",
        "Environmental Science",
    ],
    "Master of Computer Applications": ["Computer Applications"],
    "Master of Business Administration": [
        "Business Administration", "Finance", "Marketing",
        "Human Resources Management", "Operations Management",
        "International Business", "Entrepreneurship", "Banking and Finance",
    ],
    "Master of Commerce": [
        "Commerce", "Accounting", "Finance", "Banking and Finance",
    ],
    "Master of Arts": [
        "Economics", "Psychology", "Sociology", "Political Science",
        "History", "Geography", "English", "Hindi", "Mass Communication",
        "Public Administration",
    ],
    "Doctor of Philosophy": list(FIELDS.keys()),  # PhD can be in any field
}


# ─────────────────────────────────────────────────────────────────
# 3. EXPORT FUNCTIONS
# ─────────────────────────────────────────────────────────────────

def export_fields_csv():
    """Export field_of_study alias table."""
    rows = []
    for canonical, aliases in FIELDS.items():
        for alias in aliases:
            rows.append({
                "canonical_field": canonical,
                "alias": alias,
                "normalized": alias.strip().lower().replace(".", "").replace(" ", "").replace("&", "and"),
            })
    os.makedirs(r"c:\Users\arnav\Downloads\CV_SIP\cv_manager_sip\data", exist_ok=True)
    with open(r"c:\Users\arnav\Downloads\CV_SIP\cv_manager_sip\data\field_of_study_aliases.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["canonical_field", "alias", "normalized"])
        w.writeheader()
        w.writerows(rows)
    print(f"[field_of_study_aliases.csv] {len(rows)} rows, {len(FIELDS)} canonical fields")
    return rows


def export_degree_field_map_csv():
    """Export degree ↔ field mapping table."""
    rows = []
    for degree, fields in DEGREE_FIELD_MAP.items():
        for field in fields:
            rows.append({"degree_canonical": degree, "field_canonical": field})
    with open(r"c:\Users\arnav\Downloads\CV_SIP\cv_manager_sip\data\degree_field_map.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["degree_canonical", "field_canonical"])
        w.writeheader()
        w.writerows(rows)
    print(f"[degree_field_map.csv] {len(rows)} degree-field pairs")
    return rows


def export_full_reference_csv():
    """
    Export the FULL combined reference table:
    degree_type × field_of_study → all alias combinations.
    This is what a recruiter search UI would load its dropdowns from.
    """
    # Load degree aliases from previous script output
    degree_aliases = {}
    try:
        with open(r"c:\Users\arnav\Downloads\CV_SIP\cv_manager_sip\data\degree_aliases.csv") as f:
            for row in csv.DictReader(f):
                canon = row["canonical_name"]
                if canon not in degree_aliases:
                    degree_aliases[canon] = []
                degree_aliases[canon].append(row["raw_string"])
    except FileNotFoundError:
        print("[warn] degree_aliases.csv not found — skipping degree alias expansion")
        degree_aliases = {d: [d] for d in DEGREE_FIELD_MAP}

    rows = []
    for degree_canon, fields in DEGREE_FIELD_MAP.items():
        degree_aliases_list = degree_aliases.get(degree_canon, [degree_canon])
        for field_canon in fields:
            field_aliases_list = FIELDS.get(field_canon, [field_canon])
            rows.append({
                "degree_canonical": degree_canon,
                "field_canonical": field_canon,
                "degree_alias_count": len(degree_aliases_list),
                "field_alias_count": len(field_aliases_list),
                "example_resume_strings": " | ".join([
                    f"{d} in {f}" for d, f in [
                        (degree_aliases_list[0], field_aliases_list[0]),
                        (degree_aliases_list[1] if len(degree_aliases_list) > 1 else degree_aliases_list[0],
                         field_aliases_list[1] if len(field_aliases_list) > 1 else field_aliases_list[0]),
                    ]
                ])
            })

    with open(r"c:\Users\arnav\Downloads\CV_SIP\cv_manager_sip\data\full_education_reference.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["degree_canonical", "field_canonical",
                                           "degree_alias_count", "field_alias_count",
                                           "example_resume_strings"])
        w.writeheader()
        w.writerows(rows)
    print(f"[full_education_reference.csv] {len(rows)} degree-field combinations")
    return rows


def export_sql():
    """Export SQL seed statements for all three tables."""
    lines = [
        "-- ============================================================",
        "-- CV Manager — Education Reference Seed Data",
        "-- Generated by field_of_study.py",
        "-- ============================================================",
        "",
        "-- Table 1: field_of_study_aliases",
        "CREATE TABLE IF NOT EXISTS field_of_study_aliases (",
        "  id INT AUTO_INCREMENT PRIMARY KEY,",
        "  canonical_field VARCHAR(255) NOT NULL,",
        "  alias VARCHAR(255) NOT NULL,",
        "  normalized VARCHAR(255) NOT NULL,",
        "  INDEX idx_normalized (normalized),",
        "  INDEX idx_canonical (canonical_field)",
        ");",
        "",
        "INSERT INTO field_of_study_aliases (canonical_field, alias, normalized) VALUES",
    ]

    alias_rows = []
    for canonical, aliases in FIELDS.items():
        for alias in aliases:
            if not alias.strip():
                continue
            normalized = alias.strip().lower().replace(".", "").replace(" ", "").replace("&", "and")
            c = canonical.replace("'", "''")
            a = alias.replace("'", "''")
            n = normalized.replace("'", "''")
            alias_rows.append(f"  ('{c}', '{a}', '{n}')")

    lines.append(",\n".join(alias_rows) + ";")
    lines += [
        "",
        "-- Table 2: degree_field_map",
        "CREATE TABLE IF NOT EXISTS degree_field_map (",
        "  id INT AUTO_INCREMENT PRIMARY KEY,",
        "  degree_canonical VARCHAR(255) NOT NULL,",
        "  field_canonical VARCHAR(255) NOT NULL,",
        "  INDEX idx_degree (degree_canonical),",
        "  INDEX idx_field (field_canonical)",
        ");",
        "",
        "INSERT INTO degree_field_map (degree_canonical, field_canonical) VALUES",
    ]

    map_rows = []
    for degree, fields in DEGREE_FIELD_MAP.items():
        for field in fields:
            d = degree.replace("'", "''")
            fi = field.replace("'", "''")
            map_rows.append(f"  ('{d}', '{fi}')")
    lines.append(",\n".join(map_rows) + ";")

    with open(r"c:\Users\arnav\Downloads\CV_SIP\cv_manager_sip\data\education_reference_seed.sql", "w") as f:
        f.write("\n".join(lines))
    print(f"[education_reference_seed.sql] exported")


def print_summary():
    total_aliases = sum(len(v) for v in FIELDS.values())
    total_pairs = sum(len(v) for v in DEGREE_FIELD_MAP.values())
    print()
    print("=" * 60)
    print("  FIELD OF STUDY REFERENCE TABLE — Summary")
    print("=" * 60)
    print(f"  Canonical fields       : {len(FIELDS)}")
    print(f"  Total field aliases    : {total_aliases}")
    print(f"  Degree-field pairs     : {total_pairs}")
    print()
    print("  Fields by category:")
    categories = {
        "Engineering & Technology": 20,
        "Pure Sciences": 11,
        "Computer Applications": 2,
        "Management & Commerce": 10,
        "Humanities & Social Sci": 9,
        "Law": 1,
        "Medicine & Health": 6,
        "Architecture & Design": 2,
        "Education / Hospitality / Agri / Other": 4,
    }
    for cat, count in categories.items():
        print(f"    {cat:<40} {count} fields")
    print("=" * 60)
    print()
    print("  How this integrates with degree_aliases.csv:")
    print()
    print("  candidate_education table stores:")
    print("    raw_degree_string  -> normalize -> canonical_degree_id")
    print("    raw_field_string   -> normalize -> canonical_field_id")
    print()
    print("  Recruiter search:")
    print("    'B.Tech'  +  'CSE'")
    print("     | lookup     | lookup")
    print("    'Bachelor of Technology'  +  'Computer Science and Engineering'")
    print("     | query degree_field_map to validate combination")
    print("     | query candidate_education for matching candidates")
    print("=" * 60)


if __name__ == "__main__":
    print_summary()
    export_fields_csv()
    export_degree_field_map_csv()
    export_full_reference_csv()
    export_sql()
    print("\nAll files exported.")
