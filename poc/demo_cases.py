"""
Shared demo and CLI smoke-case inputs for CV Manager engines.

Keeping these inputs in one place prevents the standalone CLIs from drifting
apart and makes it obvious which examples are used for quick manual checks.
"""

STANDARD_TESTS: list[str] = [
    # Clean abbreviations
    "B.Tech",
    "BTech",
    "MBA",
    "BBA",
    "BSc",
    "12th",
    # Typo-laced
    "Bacheler of Technology",
    "Bachellor of Technolgy",
    "Bachelar of Sci",
    # With field separators
    "B. Tech in CSE",
    "M.Tech (Computer Science)",
    "B.Tech - Mechanical Engineering",
    "BE, Electronics",
    # Long canonical names
    "Bachelor of Technology",
    "Bachelor of Business Administration",
    # Abbreviated long name (the BBA bug case)
    "Bachelor of Business Admin",
    # Hons / variant markers
    "BE Hons",
    "B.Pharma",
    # Unrecognised
    "Kuchh bhi degree",
    # Conversational (L3 territory)
    "I completed my Masters in Data Science from IIT Delhi",
    "She holds a diploma in Electrical Engineering",
]


L3_UNSTRUCTURED_TESTS: list[str] = [
    # Conversational sentences
    "I completed my B.Tech in Computer Science from IIT Delhi in 2022",
    "She is pursuing her Masters in Data Science at IIM Ahmedabad",
    "He holds a Bachelor of Business Administration from DU",
    "Finished my PhD in Biotechnology last year",
    "Have a diploma in Mechanical Engineering from a polytechnic",
    # Abbreviations without context
    "BCA",
    "MBA",
    "BSc",
    "LLB",
    "PGDM",
    "BEng",
    "b.tech/be",
    # PhD variants that used to fail
    "PHD degree",
    "Ph.D with specialization",
    "DPhil Hons degree",
    # Mixed / ambiguous
    "Graduate from Computer Science department",
    "Undergraduate degree - Electrical Engineering",
    "Some random text with no educational information",
    # Already-structured (should still work)
    "B.Tech (CSE)",
    "Master of Technology in Artificial Intelligence",
    # Compact abbreviated fields
    "BTech ECE 2022",
    "Currently pursuing B.Tech in ECE from IIT",
    "B.Sc in IT from Delhi University",
]
