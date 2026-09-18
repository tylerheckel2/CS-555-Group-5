"""
CS 555 - Agile Methods for Software Development Group 5 Assignment
GEDCOM Project - Sprint 0 - Team Setup Assignment

Reads a GEDCOM file line by line, validates each line's level/tag,
and additionally stores the data about individuals and
families as it is read. After the whole file has been processed,
it prints an Individuals summary table and a Families summary table
in the style shown in the Project Overview and assignment instructions.

Usage: python gedcom_reader.py <gedcom_file>
"""

import sys
import datetime

# Line-level validation

VALID_TAGS = {
    (0, "INDI"),
    (1, "NAME"),
    (1, "SEX"),
    (1, "BIRT"),
    (1, "DEAT"),
    (1, "FAMC"),
    (1, "FAMS"),
    (0, "FAM"),
    (1, "MARR"),
    (1, "HUSB"),
    (1, "WIFE"),
    (1, "CHIL"),
    (1, "DIV"),
    (2, "DATE"),
    (0, "HEAD"),
    (0, "TRLR"),
    (0, "NOTE"),
}

ID_FIRST_TAGS = {"INDI", "FAM"}

MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def parse_line(line):
    # Parse a single GEDCOM line into (level, tag, valid, arguments).
    tokens = line.split()
    if not tokens:
        return None

    level = int(tokens[0])

    if level == 0 and len(tokens) >= 3 and tokens[2] in ID_FIRST_TAGS:
        tag = tokens[2]
        arguments = tokens[1]
    else:
        tag = tokens[1] if len(tokens) > 1 else ""
        arguments = " ".join(tokens[2:]) if len(tokens) > 2 else ""

    valid = "Y" if (level, tag) in VALID_TAGS else "N"

    return level, tag, valid, arguments


def parse_date(date_str):
    # Convert an "Exact Format" GEDCOM date ("3 MAR 1945") to a datetime.date, or None if it can't be parsed.
    if not date_str:
        return None
    parts = date_str.split()
    if len(parts) != 3:
        return None
    day_str, mon_str, year_str = parts
    month = MONTHS.get(mon_str.upper())
    if month is None:
        return None
    try:
        return datetime.date(int(year_str), month, int(day_str))
    except ValueError:
        return None


def calculate_age(birth, end):
    # Whole years between two dates, or None if either is missing.
    if birth is None or end is None:
        return None
    had_birthday = (end.month, end.day) >= (birth.month, birth.day)
    return end.year - birth.year - (0 if had_birthday else 1)


def format_id_set(ids):
    """
    Format a list of IDs the way the assignment's sample output does.
    NA if empty, otherwise a set literal like {"F23"} or {"I19", "I26"} (sorted for deterministic output).
    """
    if not ids:
        return "NA"
    return "{" + ", ".join(f"'{i}'" for i in sorted(ids)) + "}"

# Data model

class Individual:
    def __init__(self, indi_id):
        self.id = indi_id
        self.name = ""
        self.sex = ""
        self.birth_date = None
        self.death_date = None
        self.alive = True
        self.famc = []
        self.fams = []


class Family:
    def __init__(self, fam_id):
        self.id = fam_id
        self.married_date = None
        self.divorced_date = None
        self.husb = None
        self.wife = None
        self.chil = []

# Build the individuals/families collections from the parsed lines

def process_gedcom(filename):
    # Read filename, print the --> / <-- validation lines, and return (individuals, families) dicts keyed by ID.

    individuals = {}
    families = {}

    current_indi = None
    current_fam = None
    last_event = None

    with open(filename, "r", encoding="utf-8") as gedcom_file:
        for raw_line in gedcom_file:
            line = raw_line.rstrip("\r\n")
            if not line.strip():
                continue

            print(f"--> {line}")

            parsed = parse_line(line)
            if parsed is None:
                continue

            level, tag, valid, arguments = parsed
            print(f"<-- {level}|{tag}|{valid}|{arguments}")

            if level == 0:
                current_indi = None
                current_fam = None
                last_event = None

                if tag == "INDI":
                    current_indi = Individual(arguments)
                    individuals[arguments] = current_indi
                elif tag == "FAM":
                    current_fam = Family(arguments)
                    families[arguments] = current_fam

            elif level == 1:
                if current_indi is not None:
                    if tag == "NAME":
                        current_indi.name = arguments
                    elif tag == "SEX":
                        current_indi.sex = arguments
                    elif tag == "BIRT":
                        last_event = "BIRT"
                    elif tag == "DEAT":
                        last_event = "DEAT"
                        current_indi.alive = False
                    elif tag == "FAMC":
                        current_indi.famc.append(arguments)
                    elif tag == "FAMS":
                        current_indi.fams.append(arguments)

                elif current_fam is not None:
                    if tag == "HUSB":
                        current_fam.husb = arguments
                    elif tag == "WIFE":
                        current_fam.wife = arguments
                    elif tag == "CHIL":
                        current_fam.chil.append(arguments)
                    elif tag == "MARR":
                        last_event = "MARR"
                    elif tag == "DIV":
                        last_event = "DIV"

            elif level == 2:
                if tag == "DATE":
                    date_value = parse_date(arguments)
                    if last_event == "BIRT" and current_indi is not None:
                        current_indi.birth_date = date_value
                    elif last_event == "DEAT" and current_indi is not None:
                        current_indi.death_date = date_value
                    elif last_event == "MARR" and current_fam is not None:
                        current_fam.married_date = date_value
                    elif last_event == "DIV" and current_fam is not None:
                        current_fam.divorced_date = date_value

    return individuals, families


# Printing the summary tables

def print_table(headers, rows):
    # Print a simple bordered ASCII table.
    col_widths = [
        max(len(str(headers[i])), max((len(str(r[i])) for r in rows), default=0))
        for i in range(len(headers))
    ]
    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    def fmt_row(row):
        return "| " + " | ".join(
            str(row[i]).ljust(col_widths[i]) for i in range(len(row))
        ) + " |"

    print(sep)
    print(fmt_row(headers))
    print(sep)
    for row in rows:
        print(fmt_row(row))
    print(sep)


def print_individuals(individuals):
    headers = ["ID", "Name", "Gender", "Birthday", "Age", "Alive", "Death", "Child", "Spouse"]
    rows = []

    today = datetime.date.today()

    for indi_id in sorted(individuals.keys()):
        person = individuals[indi_id]

        birthday_str = person.birth_date.isoformat() if person.birth_date else "NA"
        death_str = person.death_date.isoformat() if person.death_date else "NA"

        if person.alive:
            age = calculate_age(person.birth_date, today)
        else:
            age = calculate_age(person.birth_date, person.death_date)
        age_str = age if age is not None else "NA"

        rows.append([
            person.id,
            person.name,
            person.sex,
            birthday_str,
            age_str,
            person.alive,
            death_str,
            format_id_set(person.famc),
            format_id_set(person.fams),
        ])

    print()
    print("Individuals")
    print_table(headers, rows)


def print_families(individuals, families):
    headers = ["ID", "Married", "Divorced", "Husband ID", "Husband Name",
               "Wife ID", "Wife Name", "Children"]
    rows = []

    for fam_id in sorted(families.keys()):
        family = families[fam_id]

        married_str = family.married_date.isoformat() if family.married_date else "NA"
        divorced_str = family.divorced_date.isoformat() if family.divorced_date else "NA"

        husb_id = family.husb if family.husb else "NA"
        wife_id = family.wife if family.wife else "NA"
        husb_name = individuals[family.husb].name if family.husb in individuals else "NA"
        wife_name = individuals[family.wife].name if family.wife in individuals else "NA"

        rows.append([
            family.id,
            married_str,
            divorced_str,
            husb_id,
            husb_name,
            wife_id,
            wife_name,
            format_id_set(family.chil),
        ])

    print()
    print("Families")
    print_table(headers, rows)


# Entry point

def main():
    if len(sys.argv) != 2:
        print("Usage: python gedcom_reader.py <gedcom_file>")
        sys.exit(1)

    filename = sys.argv[1]

    individuals, families = process_gedcom(filename)
    print_individuals(individuals)
    print_families(individuals, families)


if __name__ == "__main__":
    main()
