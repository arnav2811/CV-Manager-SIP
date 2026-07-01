"""Build degree-only training datasets by education system.

Outputs:
  - India + USA degree corpus
  - India + UK degree corpus
  - India + world degree corpus

The files contain degree/qualification names only. They intentionally exclude
fields of study and specializations such as Computer Science, Finance, CSE, etc.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = DATA_DIR / "training" / "degree_only"


def clean_token(raw: str) -> str:
    norm = (
        str(raw)
        .lower()
        .replace(".", "")
        .replace("-", " ")
        .replace("/", " ")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )
    return " ".join(norm.split())


def split_degree_field(raw: str) -> tuple[str, str | None]:
    text = str(raw).strip()
    m = re.split(r"\s+-\s+|\s+/\s+|\s+in\s+", text, maxsplit=1, flags=re.IGNORECASE)
    if len(m) == 2:
        return m[0].strip(), m[1].strip()
    paren = re.search(r"\((.*?)\)", text)
    if paren:
        return re.sub(r"\(.*?\)", "", text).strip(), paren.group(1).strip()
    if "," in text:
        a, b = text.split(",", 1)
        return a.strip(), b.strip()
    return text, None


def is_degree_only_alias(alias: str) -> bool:
    without_hons = re.sub(
        r"\s*\((?:hons|honours|honors)\)", "", alias, flags=re.IGNORECASE
    )
    without_hons = re.sub(
        r"\b(?:hons|honours|honors)\b", "", without_hons, flags=re.IGNORECASE
    )
    _degree, field = split_degree_field(without_hons)
    return field is None


def dotted_abbreviation(abbr: str) -> list[str]:
    token = abbr.strip()
    if not token or len(token) > 12:
        return []

    compact = re.sub(r"[^A-Za-z0-9]", "", token)
    if not compact:
        return []

    forms = {token, compact, compact.upper(), compact.lower()}

    if len(compact) <= 5 and compact.isalpha():
        forms.add(".".join(compact.upper()) + ".")
        forms.add(" ".join(compact.upper()))
        forms.add("-".join(compact.upper()))

    patterns = {
        "BTECH": ["B.Tech", "B. Tech", "B Tech", "B-Tech", "B.Tech."],
        "MTECH": ["M.Tech", "M. Tech", "M Tech", "M-Tech", "M.Tech."],
        "BSC": ["B.Sc", "B. Sc", "B Sc", "B.Sc."],
        "MSC": ["M.Sc", "M. Sc", "M Sc", "M.Sc."],
        "BA": ["B.A", "B. A", "B A", "B.A."],
        "MA": ["M.A", "M. A", "M A", "M.A."],
        "BCOM": ["B.Com", "B. Com", "B Com", "B.Com."],
        "MCOM": ["M.Com", "M. Com", "M Com", "M.Com."],
        "BBA": ["B.B.A", "B. B. A", "B B A", "BBA"],
        "MBA": ["M.B.A", "M. B. A", "M B A", "MBA"],
        "BCA": ["B.C.A", "B. C. A", "B C A", "BCA"],
        "MCA": ["M.C.A", "M. C. A", "M C A", "MCA"],
        "PHD": ["PhD", "Ph.D", "Ph. D.", "Doctorate"],
        "LLB": ["LLB", "L.L.B", "LL.B", "L L B"],
        "LLM": ["LLM", "L.L.M", "LL.M", "L L M"],
        "PGD": ["PGD", "P.G.D", "PG Diploma", "Post Grad Diploma"],
        "PGDM": ["PGDM", "P.G.D.M", "PG Diploma Management"],
    }
    forms.update(patterns.get(compact.upper(), []))
    return sorted(forms)


def degree_family(canonical: str, level: str) -> str:
    text = f"{canonical} {level}".lower()
    if "doctor" in text or "phd" in text or "dphil" in text:
        return "doctoral"
    if "master" in text or "postgraduate" in text or "post graduate" in text:
        return "postgraduate"
    if "bachelor" in text or "undergraduate" in text or "honours" in text:
        return "undergraduate"
    if "associate" in text or "short cycle" in text:
        return "short_cycle"
    if "diploma" in text or "certificate" in text:
        return "diploma_certificate"
    if "school" in text or "secondary" in text or "standard" in text:
        return "school"
    return "professional"


def entry(
    system_id: str,
    country_system: str,
    country_code: str,
    region: str,
    canonical_degree: str,
    level: str,
    short_code: str,
    aliases: list[str],
    duration_hint: str = "",
    local_level: str = "",
    source_note: str = "curated_degree_system_catalog",
) -> dict:
    all_aliases = [canonical_degree, short_code, *aliases]
    deduped_aliases = []
    seen = set()
    for alias in all_aliases:
        alias = str(alias).strip()
        if alias and alias.lower() not in seen:
            seen.add(alias.lower())
            deduped_aliases.append(alias)

    return {
        "system_id": system_id,
        "country_system": country_system,
        "country_code": country_code,
        "region": region,
        "canonical_degree": canonical_degree,
        "qualification_level": level,
        "degree_family": degree_family(canonical_degree, level),
        "short_code": short_code,
        "aliases": deduped_aliases,
        "duration_hint": duration_hint,
        "local_level": local_level,
        "source_note": source_note,
    }


def load_india_entries() -> list[dict]:
    degree_dict = json.loads((DATA_DIR / "degree_dictionary.json").read_text(encoding="utf-8"))
    rows = []
    for idx, (canonical, meta) in enumerate(sorted(degree_dict.items()), 1):
        short_code = meta.get("short_code", "")
        aliases = [
            alias
            for alias in meta.get("aliases", [])
            if is_degree_only_alias(alias)
        ]
        rows.append(
            entry(
                f"IN-{idx:03d}",
                "India",
                "IN",
                "South Asia",
                canonical,
                meta.get("level", ""),
                short_code,
                aliases,
                duration_hint=duration_for(canonical),
                local_level=meta.get("level", ""),
                source_note="data/degree_dictionary.json filtered to degree-only aliases",
            )
        )
    return rows


def duration_for(canonical: str) -> str:
    text = canonical.lower()
    if "doctor" in text or "philosophy" in text:
        return "3-6 years"
    if "master" in text:
        return "1-2 years"
    if "bachelor" in text:
        return "3-4 years"
    if "post graduate diploma" in text:
        return "1-2 years"
    if "diploma" in text:
        return "1-3 years"
    if "12th" in text or "10th" in text:
        return "school qualification"
    return ""


USA_ENTRIES = [
    entry("US-001", "United States", "US", "North America", "High School Diploma", "Secondary", "HSD", ["US High School Diploma", "Secondary School Diploma"], "4 years"),
    entry("US-002", "United States", "US", "North America", "General Educational Development", "Secondary Equivalency", "GED", ["GED", "GED Diploma"], ""),
    entry("US-003", "United States", "US", "North America", "Associate of Arts", "Associate", "AA", ["A.A.", "Associate Arts"], "2 years"),
    entry("US-004", "United States", "US", "North America", "Associate of Science", "Associate", "AS", ["A.S.", "Associate Science"], "2 years"),
    entry("US-005", "United States", "US", "North America", "Associate of Applied Science", "Associate", "AAS", ["A.A.S.", "Applied Science Associate"], "2 years"),
    entry("US-006", "United States", "US", "North America", "Bachelor of Arts", "Undergraduate", "BA", ["B.A.", "AB", "Artium Baccalaureus"], "4 years"),
    entry("US-007", "United States", "US", "North America", "Bachelor of Science", "Undergraduate", "BS", ["B.S.", "ScB", "Bachelor Science"], "4 years"),
    entry("US-008", "United States", "US", "North America", "Bachelor of Fine Arts", "Undergraduate", "BFA", ["B.F.A.", "Fine Arts Bachelor"], "4 years"),
    entry("US-009", "United States", "US", "North America", "Bachelor of Business Administration", "Undergraduate", "BBA", ["B.B.A.", "Business Administration Bachelor"], "4 years"),
    entry("US-010", "United States", "US", "North America", "Bachelor of Engineering", "Undergraduate", "BE", ["B.E.", "BEng", "B.Eng."], "4 years"),
    entry("US-011", "United States", "US", "North America", "Bachelor of Architecture", "Undergraduate", "BArch", ["B.Arch", "B.Arch."], "5 years"),
    entry("US-012", "United States", "US", "North America", "Bachelor of Music", "Undergraduate", "BM", ["B.M.", "BMus"], "4 years"),
    entry("US-013", "United States", "US", "North America", "Bachelor of Social Work", "Undergraduate", "BSW", ["B.S.W."], "4 years"),
    entry("US-014", "United States", "US", "North America", "Master of Arts", "Graduate", "MA", ["M.A.", "AM", "Artium Magister"], "1-2 years"),
    entry("US-015", "United States", "US", "North America", "Master of Science", "Graduate", "MS", ["M.S.", "SM", "ScM"], "1-2 years"),
    entry("US-016", "United States", "US", "North America", "Master of Business Administration", "Graduate", "MBA", ["M.B.A."], "1-2 years"),
    entry("US-017", "United States", "US", "North America", "Master of Engineering", "Graduate", "MEng", ["M.Eng.", "ME", "M.E."], "1-2 years"),
    entry("US-018", "United States", "US", "North America", "Master of Fine Arts", "Graduate", "MFA", ["M.F.A."], "2-3 years"),
    entry("US-019", "United States", "US", "North America", "Master of Public Health", "Graduate", "MPH", ["M.P.H."], "1-2 years"),
    entry("US-020", "United States", "US", "North America", "Master of Public Administration", "Graduate", "MPA", ["M.P.A."], "1-2 years"),
    entry("US-021", "United States", "US", "North America", "Master of Social Work", "Graduate", "MSW", ["M.S.W."], "1-2 years"),
    entry("US-022", "United States", "US", "North America", "Juris Doctor", "Professional Doctorate", "JD", ["J.D.", "Doctor of Jurisprudence"], "3 years"),
    entry("US-023", "United States", "US", "North America", "Doctor of Medicine", "Professional Doctorate", "MD", ["M.D."], "4 years"),
    entry("US-024", "United States", "US", "North America", "Doctor of Dental Surgery", "Professional Doctorate", "DDS", ["D.D.S."], "4 years"),
    entry("US-025", "United States", "US", "North America", "Doctor of Pharmacy", "Professional Doctorate", "PharmD", ["Pharm.D."], "4 years"),
    entry("US-026", "United States", "US", "North America", "Doctor of Nursing Practice", "Professional Doctorate", "DNP", ["D.N.P."], "3-4 years"),
    entry("US-027", "United States", "US", "North America", "Doctor of Philosophy", "Doctoral", "PhD", ["Ph.D.", "Ph.D", "Doctorate"], "4-7 years"),
    entry("US-028", "United States", "US", "North America", "Doctor of Education", "Doctoral", "EdD", ["Ed.D."], "3-5 years"),
    entry("US-029", "United States", "US", "North America", "Doctor of Business Administration", "Doctoral", "DBA", ["D.B.A."], "3-5 years"),
    entry("US-030", "United States", "US", "North America", "Doctor of Psychology", "Doctoral", "PsyD", ["Psy.D."], "4-6 years"),
]


UK_ENTRIES = [
    entry("UK-001", "United Kingdom", "UK", "Europe", "General Certificate of Secondary Education", "Secondary", "GCSE", ["GCSEs", "GCSE"], "2 years"),
    entry("UK-002", "United Kingdom", "UK", "Europe", "Advanced Level", "Secondary", "A Level", ["A-Level", "A Levels", "GCE A Level"], "2 years"),
    entry("UK-003", "United Kingdom", "UK", "Europe", "Certificate of Higher Education", "Higher Education Certificate", "CertHE", ["Cert HE"], "1 year"),
    entry("UK-004", "United Kingdom", "UK", "Europe", "Diploma of Higher Education", "Higher Education Diploma", "DipHE", ["Dip HE"], "2 years"),
    entry("UK-005", "United Kingdom", "UK", "Europe", "Higher National Certificate", "Higher Education Certificate", "HNC", ["H.N.C."], "1 year"),
    entry("UK-006", "United Kingdom", "UK", "Europe", "Higher National Diploma", "Higher Education Diploma", "HND", ["H.N.D."], "2 years"),
    entry("UK-007", "United Kingdom", "UK", "Europe", "Foundation Degree", "Undergraduate", "Fd", ["FdA", "FdSc", "Foundation Degree Arts", "Foundation Degree Science"], "2 years"),
    entry("UK-008", "United Kingdom", "UK", "Europe", "Bachelor of Arts", "Undergraduate", "BA", ["B.A.", "BA Hons", "Bachelor of Arts with Honours"], "3-4 years"),
    entry("UK-009", "United Kingdom", "UK", "Europe", "Bachelor of Science", "Undergraduate", "BSc", ["B.Sc.", "BSc Hons", "Bachelor of Science with Honours"], "3-4 years"),
    entry("UK-010", "United Kingdom", "UK", "Europe", "Bachelor of Engineering", "Undergraduate", "BEng", ["B.Eng.", "BEng Hons"], "3-4 years"),
    entry("UK-011", "United Kingdom", "UK", "Europe", "Master of Engineering", "Integrated Masters", "MEng", ["M.Eng.", "MEng Hons"], "4 years"),
    entry("UK-012", "United Kingdom", "UK", "Europe", "Bachelor of Laws", "Undergraduate", "LLB", ["LL.B.", "Bachelor of Law"], "3 years"),
    entry("UK-013", "United Kingdom", "UK", "Europe", "Bachelor of Medicine Bachelor of Surgery", "Professional Degree", "MBBS", ["MB ChB", "MBChB", "BMBS", "MBBCh"], "5-6 years"),
    entry("UK-014", "United Kingdom", "UK", "Europe", "Master of Arts", "Postgraduate", "MA", ["M.A."], "1-2 years"),
    entry("UK-015", "United Kingdom", "UK", "Europe", "Master of Science", "Postgraduate", "MSc", ["M.Sc."], "1-2 years"),
    entry("UK-016", "United Kingdom", "UK", "Europe", "Master of Research", "Postgraduate", "MRes", ["M.Res."], "1 year"),
    entry("UK-017", "United Kingdom", "UK", "Europe", "Master of Philosophy", "Postgraduate Research", "MPhil", ["M.Phil."], "1-2 years"),
    entry("UK-018", "United Kingdom", "UK", "Europe", "Master of Laws", "Postgraduate", "LLM", ["LL.M."], "1 year"),
    entry("UK-019", "United Kingdom", "UK", "Europe", "Master of Business Administration", "Postgraduate", "MBA", ["M.B.A."], "1-2 years"),
    entry("UK-020", "United Kingdom", "UK", "Europe", "Postgraduate Certificate", "Postgraduate Certificate", "PGCert", ["PG Cert", "P.G.Cert."], "less than 1 year"),
    entry("UK-021", "United Kingdom", "UK", "Europe", "Postgraduate Diploma", "Postgraduate Diploma", "PGDip", ["PG Dip", "P.G.Dip."], "1 year"),
    entry("UK-022", "United Kingdom", "UK", "Europe", "Doctor of Philosophy", "Doctoral", "PhD", ["Ph.D.", "DPhil", "D.Phil."], "3-4 years"),
    entry("UK-023", "United Kingdom", "UK", "Europe", "Doctor of Education", "Doctoral", "EdD", ["Ed.D."], "3-5 years"),
    entry("UK-024", "United Kingdom", "UK", "Europe", "Doctor of Business Administration", "Doctoral", "DBA", ["D.B.A."], "3-5 years"),
]


WORLD_EXTRA_ENTRIES = [
    entry("CA-001", "Canada", "CA", "North America", "Ontario Secondary School Diploma", "Secondary", "OSSD", ["Canadian High School Diploma"], "4 years"),
    entry("CA-002", "Canada", "CA", "North America", "College Diploma", "Diploma", "Diploma", ["Canadian College Diploma"], "2 years"),
    entry("CA-003", "Canada", "CA", "North America", "Advanced Diploma", "Advanced Diploma", "AdvDip", ["Advanced College Diploma"], "3 years"),
    entry("CA-004", "Canada", "CA", "North America", "Bachelor of Commerce", "Undergraduate", "BCom", ["B.Com.", "BComm"], "4 years"),
    entry("CA-005", "Canada", "CA", "North America", "Master of Applied Science", "Graduate", "MASc", ["M.A.Sc."], "2 years"),
    entry("AU-001", "Australia", "AU", "Oceania", "Senior Secondary Certificate of Education", "Secondary", "SSCE", ["Year 12 Certificate"], "2 years"),
    entry("AU-002", "Australia", "AU", "Oceania", "Certificate III", "Certificate", "Cert III", ["Certificate 3"], ""),
    entry("AU-003", "Australia", "AU", "Oceania", "Certificate IV", "Certificate", "Cert IV", ["Certificate 4"], ""),
    entry("AU-004", "Australia", "AU", "Oceania", "Advanced Diploma", "Advanced Diploma", "AdvDip", ["Advanced Diploma Australia"], "1.5-2 years"),
    entry("AU-005", "Australia", "AU", "Oceania", "Bachelor Honours Degree", "Undergraduate Honours", "BHon", ["Bachelor with Honours"], "1 year after bachelor"),
    entry("AU-006", "Australia", "AU", "Oceania", "Graduate Certificate", "Graduate Certificate", "GradCert", ["Graduate Cert"], "6 months"),
    entry("AU-007", "Australia", "AU", "Oceania", "Graduate Diploma", "Graduate Diploma", "GradDip", ["Graduate Dip"], "1 year"),
    entry("AU-008", "Australia", "AU", "Oceania", "Doctoral Degree", "Doctoral", "PhD", ["Doctorate", "Doctor of Philosophy"], "3-4 years"),
    entry("NZ-001", "New Zealand", "NZ", "Oceania", "National Certificate of Educational Achievement Level 3", "Secondary", "NCEA Level 3", ["NCEA 3"], ""),
    entry("NZ-002", "New Zealand", "NZ", "Oceania", "New Zealand Diploma", "Diploma", "NZDip", ["NZ Diploma"], ""),
    entry("EU-001", "European Higher Education Area", "EU", "Europe", "Short Cycle Qualification", "Short Cycle", "SCQF", ["Bologna Short Cycle"], ""),
    entry("EU-002", "European Higher Education Area", "EU", "Europe", "Bachelor Degree", "First Cycle", "BA/BSc", ["Bologna Bachelor", "First Cycle Degree"], "3-4 years"),
    entry("EU-003", "European Higher Education Area", "EU", "Europe", "Master Degree", "Second Cycle", "MA/MSc", ["Bologna Master", "Second Cycle Degree"], "1-2 years"),
    entry("EU-004", "European Higher Education Area", "EU", "Europe", "Doctoral Degree", "Third Cycle", "PhD", ["Bologna Doctorate", "Third Cycle Degree"], "3-4 years"),
    entry("DE-001", "Germany", "DE", "Europe", "Abitur", "Secondary", "Abitur", ["Allgemeine Hochschulreife"], ""),
    entry("DE-002", "Germany", "DE", "Europe", "Bachelor of Engineering", "Undergraduate", "BEng", ["B.Eng."], "3-4 years"),
    entry("DE-003", "Germany", "DE", "Europe", "Master of Engineering", "Postgraduate", "MEng", ["M.Eng."], "1-2 years"),
    entry("DE-004", "Germany", "DE", "Europe", "Staatsexamen", "Professional Degree", "StEx", ["State Examination"], ""),
    entry("DE-005", "Germany", "DE", "Europe", "Diplom", "Legacy Degree", "Dipl.", ["Diplom Degree"], ""),
    entry("DE-006", "Germany", "DE", "Europe", "Magister Artium", "Legacy Degree", "MA", ["M.A.", "Magister"], ""),
    entry("FR-001", "France", "FR", "Europe", "Baccalaureat", "Secondary", "Bac", ["French Baccalaureate"], ""),
    entry("FR-002", "France", "FR", "Europe", "Brevet de Technicien Superieur", "Short Cycle", "BTS", ["B.T.S."], "2 years"),
    entry("FR-003", "France", "FR", "Europe", "Licence", "Undergraduate", "Licence", ["French Licence"], "3 years"),
    entry("FR-004", "France", "FR", "Europe", "Licence Professionnelle", "Undergraduate Professional", "LP", ["Professional Licence"], "1 year after Bac+2"),
    entry("FR-005", "France", "FR", "Europe", "Master", "Postgraduate", "Master", ["French Master"], "2 years"),
    entry("FR-006", "France", "FR", "Europe", "Diplome d'Ingenieur", "Engineering Degree", "Ing", ["Engineering Diploma France"], "5 years"),
    entry("FR-007", "France", "FR", "Europe", "Doctorat", "Doctoral", "PhD", ["French Doctorate"], "3 years"),
    entry("IT-001", "Italy", "IT", "Europe", "Diploma di Maturita", "Secondary", "Maturita", ["Italian High School Diploma"], ""),
    entry("IT-002", "Italy", "IT", "Europe", "Laurea Triennale", "Undergraduate", "LT", ["First Cycle Laurea"], "3 years"),
    entry("IT-003", "Italy", "IT", "Europe", "Laurea Magistrale", "Postgraduate", "LM", ["Second Cycle Laurea"], "2 years"),
    entry("IT-004", "Italy", "IT", "Europe", "Laurea Magistrale a Ciclo Unico", "Integrated Masters", "LMCU", ["Single Cycle Degree"], "5-6 years"),
    entry("IT-005", "Italy", "IT", "Europe", "Dottorato di Ricerca", "Doctoral", "PhD", ["Italian Doctorate"], "3 years"),
    entry("ES-001", "Spain", "ES", "Europe", "Bachillerato", "Secondary", "Bachillerato", ["Spanish Baccalaureate"], ""),
    entry("ES-002", "Spain", "ES", "Europe", "Titulo de Grado", "Undergraduate", "Grado", ["Spanish Bachelor Degree"], "4 years"),
    entry("ES-003", "Spain", "ES", "Europe", "Master Universitario", "Postgraduate", "Master", ["Official Master's Degree"], "1-2 years"),
    entry("ES-004", "Spain", "ES", "Europe", "Doctorado", "Doctoral", "PhD", ["Spanish Doctorate"], "3 years"),
    entry("NL-001", "Netherlands", "NL", "Europe", "VWO Diploma", "Secondary", "VWO", ["Pre University Diploma"], ""),
    entry("NL-002", "Netherlands", "NL", "Europe", "HBO Bachelor", "Undergraduate", "HBO B", ["University of Applied Sciences Bachelor"], "4 years"),
    entry("NL-003", "Netherlands", "NL", "Europe", "WO Bachelor", "Undergraduate", "WO B", ["Research University Bachelor"], "3 years"),
    entry("NL-004", "Netherlands", "NL", "Europe", "HBO Master", "Postgraduate", "HBO M", ["Applied Sciences Master"], "1-2 years"),
    entry("NL-005", "Netherlands", "NL", "Europe", "WO Master", "Postgraduate", "WO M", ["Research University Master"], "1-2 years"),
    entry("CN-001", "China", "CN", "East Asia", "Zhuanke Diploma", "Short Cycle", "Zhuanke", ["College Diploma China"], "2-3 years"),
    entry("CN-002", "China", "CN", "East Asia", "Bachelor Degree", "Undergraduate", "Xueshi", ["Chinese Bachelor"], "4 years"),
    entry("CN-003", "China", "CN", "East Asia", "Master Degree", "Postgraduate", "Shuoshi", ["Chinese Master"], "2-3 years"),
    entry("CN-004", "China", "CN", "East Asia", "Doctoral Degree", "Doctoral", "Boshi", ["Chinese Doctorate"], "3-4 years"),
    entry("JP-001", "Japan", "JP", "East Asia", "Associate Degree", "Short Cycle", "Associate", ["Junior College Associate Degree"], "2 years"),
    entry("JP-002", "Japan", "JP", "East Asia", "Bachelor's Degree", "Undergraduate", "Gakushi", ["Japanese Bachelor"], "4 years"),
    entry("JP-003", "Japan", "JP", "East Asia", "Master's Degree", "Postgraduate", "Shushi", ["Japanese Master"], "2 years"),
    entry("JP-004", "Japan", "JP", "East Asia", "Doctoral Degree", "Doctoral", "Hakushi", ["Japanese Doctorate"], "3-5 years"),
    entry("SG-001", "Singapore", "SG", "Southeast Asia", "GCE Ordinary Level", "Secondary", "GCE O-Level", ["O Level", "O-Level"], ""),
    entry("SG-002", "Singapore", "SG", "Southeast Asia", "GCE Advanced Level", "Secondary", "GCE A-Level", ["A Level", "A-Level"], ""),
    entry("SG-003", "Singapore", "SG", "Southeast Asia", "Polytechnic Diploma", "Diploma", "Poly Diploma", ["Singapore Polytechnic Diploma"], "3 years"),
    entry("ZA-001", "South Africa", "ZA", "Africa", "National Senior Certificate", "Secondary", "NSC", ["Matric Certificate"], ""),
    entry("ZA-002", "South Africa", "ZA", "Africa", "Higher Certificate", "Certificate", "HC", ["Higher Cert"], "1 year"),
    entry("ZA-003", "South Africa", "ZA", "Africa", "Advanced Diploma", "Advanced Diploma", "AdvDip", ["Advanced Diploma South Africa"], "1 year"),
    entry("ZA-004", "South Africa", "ZA", "Africa", "Honours Degree", "Postgraduate", "Hons", ["Bachelor Honours"], "1 year"),
    entry("BR-001", "Brazil", "BR", "South America", "Ensino Medio", "Secondary", "EM", ["Brazilian High School"], ""),
    entry("BR-002", "Brazil", "BR", "South America", "Bacharelado", "Undergraduate", "Bacharel", ["Bachelor Brazil"], "4-5 years"),
    entry("BR-003", "Brazil", "BR", "South America", "Licenciatura", "Undergraduate Teaching", "Lic.", ["Teaching Degree Brazil"], "3-4 years"),
    entry("BR-004", "Brazil", "BR", "South America", "Tecnologo", "Short Cycle", "Tecnologo", ["Technology Degree Brazil"], "2-3 years"),
    entry("BR-005", "Brazil", "BR", "South America", "Especializacao", "Postgraduate Certificate", "Esp.", ["Lato Sensu Specialization"], "1-2 years"),
    entry("BR-006", "Brazil", "BR", "South America", "Mestrado", "Postgraduate", "MSc", ["Brazilian Masters"], "2 years"),
    entry("BR-007", "Brazil", "BR", "South America", "Doutorado", "Doctoral", "PhD", ["Brazilian Doctorate"], "4 years"),
]


def case_variants(text: str) -> list[tuple[str, str]]:
    variants = [
        ("as_catalogued", text),
        ("lowercase", text.lower()),
        ("uppercase", text.upper()),
        ("title_case", text.title()),
    ]
    seen = set()
    out = []
    for name, value in variants:
        if value not in seen:
            seen.add(value)
            out.append((name, value))
    return out


def context_prefixes(item: dict) -> list[tuple[str, str]]:
    country = item["country_system"]
    code = item["country_code"]
    adjective = {
        "India": "Indian",
        "United States": "US",
        "United Kingdom": "UK",
        "Canada": "Canadian",
        "Australia": "Australian",
        "New Zealand": "New Zealand",
        "Germany": "German",
        "France": "French",
        "Italy": "Italian",
        "Spain": "Spanish",
        "Netherlands": "Dutch",
        "China": "Chinese",
        "Japan": "Japanese",
        "Singapore": "Singapore",
        "South Africa": "South African",
        "Brazil": "Brazilian",
        "European Higher Education Area": "Bologna",
    }.get(country, country)
    return [
        ("none", ""),
        ("country_adjective", adjective),
        ("country_name", country),
        ("country_code", code),
    ]


def context_suffixes(item: dict) -> list[tuple[str, str]]:
    country = item["country_system"]
    code = item["country_code"]
    duration = item["duration_hint"]
    family = item["degree_family"]
    suffixes = [
        ("none", ""),
        ("degree_word", "degree" if family not in {"school", "diploma_certificate"} else "qualification"),
        ("qualification_word", "qualification"),
        ("country_parenthetical", f"({country})"),
        ("country_dash", f"- {country}"),
        ("country_code_parenthetical", f"({code})"),
    ]
    if duration:
        suffixes.append(("duration_parenthetical", f"({duration})"))
    if family == "undergraduate":
        suffixes.extend(
            [
                ("hons_short", "(Hons)"),
                ("honours_long", "with Honours"),
            ]
        )
    return suffixes


def alias_variants(item: dict) -> list[tuple[str, str]]:
    variants = []
    for alias in item["aliases"]:
        variants.append(("alias", alias))
        if alias == item["short_code"]:
            for form in dotted_abbreviation(alias):
                variants.append(("abbreviation_permutation", form))
        elif len(alias) <= 12 and re.fullmatch(r"[A-Za-z0-9.\- ]+", alias):
            for form in dotted_abbreviation(alias):
                variants.append(("abbreviation_permutation", form))

    deduped = []
    seen = set()
    for kind, value in variants:
        key = clean_token(value)
        if value and key not in seen:
            seen.add(key)
            deduped.append((kind, value))
    return deduped


def join_parts(prefix: str, alias: str, suffix: str) -> str:
    parts = []
    if prefix:
        parts.append(prefix)
    parts.append(alias)
    if suffix:
        if suffix.startswith("(") or suffix.startswith("-"):
            return " ".join(parts) + " " + suffix
        parts.append(suffix)
    return " ".join(parts)


def build_rows(entries: list[dict], dataset_id: str, included_systems: str) -> list[dict]:
    rows = []
    seen = set()
    for item in entries:
        for alias_kind, alias in alias_variants(item):
            for prefix_kind, prefix in context_prefixes(item):
                for suffix_kind, suffix in context_suffixes(item):
                    for case_kind, cased in case_variants(join_parts(prefix, alias, suffix)):
                        raw = " ".join(cased.split())
                        key = (
                            dataset_id,
                            item["system_id"],
                            clean_token(raw),
                            item["canonical_degree"],
                        )
                        if key in seen:
                            continue
                        seen.add(key)
                        rows.append(
                            {
                                "sample_id": f"{dataset_id}-{len(rows) + 1:06d}",
                                "dataset_id": dataset_id,
                                "included_systems": included_systems,
                                "raw_input": raw,
                                "normalized_input": clean_token(raw),
                                "canonical_degree": item["canonical_degree"],
                                "canonical_country_system": item["country_system"],
                                "country_code": item["country_code"],
                                "region": item["region"],
                                "qualification_level": item["qualification_level"],
                                "degree_family": item["degree_family"],
                                "short_code": item["short_code"],
                                "duration_hint": item["duration_hint"],
                                "local_level": item["local_level"],
                                "variant_alias_kind": alias_kind,
                                "variant_prefix_kind": prefix_kind,
                                "variant_suffix_kind": suffix_kind,
                                "variant_case_kind": case_kind,
                                "expected_status": "resolved",
                                "expected_layer": "degree_only_lookup_or_fuzzy",
                                "is_degree_only": "true",
                                "source_note": item["source_note"],
                            }
                        )

    normalized_counter = Counter(row["normalized_input"] for row in rows)
    systems_by_norm = defaultdict(set)
    degrees_by_norm = defaultdict(set)
    for row in rows:
        systems_by_norm[row["normalized_input"]].add(row["canonical_country_system"])
        degrees_by_norm[row["normalized_input"]].add(row["canonical_degree"])

    for row in rows:
        norm = row["normalized_input"]
        row["is_ambiguous_across_systems"] = str(len(systems_by_norm[norm]) > 1).lower()
        row["is_ambiguous_across_degrees"] = str(len(degrees_by_norm[norm]) > 1).lower()
        row["duplicate_normalized_count"] = normalized_counter[norm]

    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_catalog(path: Path, entries: list[dict]) -> None:
    rows = []
    for item in entries:
        row = {k: v for k, v in item.items() if k != "aliases"}
        row["degree_only_alias_count"] = len(alias_variants(item))
        row["degree_only_aliases"] = " | ".join(alias for _kind, alias in alias_variants(item))
        rows.append(row)
    write_csv(path, rows)


def main() -> None:
    india_entries = load_india_entries()
    all_entries = india_entries + USA_ENTRIES + UK_ENTRIES + WORLD_EXTRA_ENTRIES

    datasets = {
        "IND_USA": (
            india_entries + USA_ENTRIES,
            "India + United States",
            OUT_DIR / "indian_usa_degrees_training.csv",
        ),
        "IND_UK": (
            india_entries + UK_ENTRIES,
            "India + United Kingdom",
            OUT_DIR / "indian_uk_degrees_training.csv",
        ),
        "IND_WORLD": (
            all_entries,
            "India + United States + United Kingdom + curated world systems",
            OUT_DIR / "indian_world_degrees_training.csv",
        ),
    }

    manifest = {
        "generated_on": date.today().isoformat(),
        "scope": "Degree/qualification names only. Fields of study and specializations are excluded.",
        "permutation_definition": [
            "degree-only aliases",
            "abbreviation punctuation/spacing variants",
            "country adjective/name/code prefixes",
            "qualification/degree/country/duration/honours suffixes",
            "catalogued/lowercase/uppercase/title-case variants",
        ],
        "source_files": [
            "data/degree_dictionary.json for India, filtered to degree-only aliases",
            "curated USA/UK/world degree-system catalog inside tools/build_degree_system_training_datasets.py",
        ],
        "datasets": {},
    }

    all_written_rows = []
    for dataset_id, (entries, included_systems, path) in datasets.items():
        rows = build_rows(entries, dataset_id, included_systems)
        write_csv(path, rows)
        all_written_rows.extend(rows)
        manifest["datasets"][path.name] = {
            "rows": len(rows),
            "canonical_entries": len(entries),
            "included_systems": included_systems,
        }
        print(f"{path.name}: {len(rows):,} rows from {len(entries):,} canonical entries")

    write_catalog(OUT_DIR / "degree_only_canonical_catalog.csv", all_entries)
    (OUT_DIR / "degree_only_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    readme = f"""# Degree-Only Country/System Training Files

Generated on {date.today().isoformat()}.

These corpora contain degree or qualification names only. They exclude fields of
study and specializations.

## Files

| File | Purpose |
|---|---|
| indian_usa_degrees_training.csv | India + USA degree-name training variants |
| indian_uk_degrees_training.csv | India + UK degree-name training variants |
| indian_world_degrees_training.csv | India + USA + UK + broader world degree-name variants |
| degree_only_canonical_catalog.csv | Canonical country/system degree catalog used by the generator |
| degree_only_manifest.json | Row counts, scope, and permutation definition |

## Permutation Rules

Each training file contains every generated combination of:
- degree-only aliases
- abbreviation punctuation and spacing forms
- country adjective, country name, and country code prefixes
- degree/qualification, country, duration, and honours suffixes
- catalogued, lowercase, uppercase, and title-case variants

Because global qualifications are open-ended, \"every permutation\" means every
permutation over this curated canonical catalog and the deterministic rules in
`tools/build_degree_system_training_datasets.py`.
"""
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")

    print(f"Wrote degree-only datasets to: {OUT_DIR}")


if __name__ == "__main__":
    main()
