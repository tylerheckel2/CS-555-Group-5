"""
CS 555 - Agile Methods for Software Development Group 5 Assignment
GEDCOM Project - Sprint 1

Reads a GEDCOM file line by line, validates each line's level/tag,
and additionally stores the data about individuals and
families as it is read. After the whole file has been processed,
it prints an Individuals summary table and a Families summary table, and then checks 
the data against our user stories.
 
Each violation is printed as a single line in the form:
 
ERROR: INDIVIDUAL|FAMILY: <StoryID>: <line#>: <id>: <description>

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


def calculate_age(start, end):
    # Whole years between two dates, or None if either is missing.
    if start is None or end is None:
        return None
    had_anniversary = (end.month, end.day) >= (start.month, start.day)
    return end.year - start.year - (0 if had_anniversary else 1)


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
    def __init__(self, indi_id, line_no):
        self.id = indi_id
        self.line_no = line_no
        self.name = ""
        self.sex = ""
        self.birth_date = None
        self.birth_line = None
        self.death_date = None
        self.death_line = None
        self.alive = True
        self.famc = []
        self.fams = []


class Family:
    def __init__(self, fam_id, line_no):
        self.id = fam_id
        self.line_no = line_no
        self.married_date = None
        self.married_line = None
        self.divorced_date = None
        self.divorced_line = None
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
        for line_no, raw_line in enumerate(gedcom_file, start=1):
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
                    current_indi = Individual(arguments, line_no)
                    individuals[arguments] = current_indi
                elif tag == "FAM":
                    current_fam = Family(arguments, line_no)
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
                        current_indi.birth_line = line_no
                    elif last_event == "DEAT" and current_indi is not None:
                        current_indi.death_date = date_value
                        current_indi.death_line = line_no
                    elif last_event == "MARR" and current_fam is not None:
                        current_fam.married_date = date_value
                        current_fam.married_line = line_no
                    elif last_event == "DIV" and current_fam is not None:
                        current_fam.divorced_date = date_value
                        current_fam.divorced_line = line_no

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


# Sprint 1 user story checks

def check_us01_dates_before_current_date(individuals, families, today):
    """US01: Dates (birth, marriage, divorce, death) should not be
    after the current date."""
    errors = []
 
    for person in individuals.values():
        if person.birth_date and person.birth_date > today:
            errors.append((person.birth_line,
                f"ERROR: INDIVIDUAL: US01: {person.birth_line}: {person.id}: "
                f"Birthday {person.birth_date} occurs in the future"))
        if person.death_date and person.death_date > today:
            errors.append((person.death_line,
                f"ERROR: INDIVIDUAL: US01: {person.death_line}: {person.id}: "
                f"Death {person.death_date} occurs in the future"))
 
    for family in families.values():
        if family.married_date and family.married_date > today:
            errors.append((family.married_line,
                f"ERROR: FAMILY: US01: {family.married_line}: {family.id}: "
                f"Marriage date {family.married_date} occurs in the future"))
        if family.divorced_date and family.divorced_date > today:
            errors.append((family.divorced_line,
                f"ERROR: FAMILY: US01: {family.divorced_line}: {family.id}: "
                f"Divorce date {family.divorced_date} occurs in the future"))
 
    return errors
 
 
def check_us02_birth_before_marriage(individuals, families):
    """US02: Birth should occur before marriage of an individual."""
    errors = []

    for family in families.values():
        if family.married_date is None:
            continue

        husband = individuals.get(family.husb)
        if husband and husband.birth_date:
            if husband.birth_date >= family.married_date:
                errors.append((
                    family.married_line,
                    f"ERROR: FAMILY: US02: {family.married_line}: {family.id}: "
                    f"Husband ({husband.id}) birth date {husband.birth_date} "
                    f"occurs on or after marriage date {family.married_date}"
                ))

        wife = individuals.get(family.wife)
        if wife and wife.birth_date:
            if wife.birth_date >= family.married_date:
                errors.append((
                    family.married_line,
                    f"ERROR: FAMILY: US02: {family.married_line}: {family.id}: "
                    f"Wife ({wife.id}) birth date {wife.birth_date} "
                    f"occurs on or after marriage date {family.married_date}"
                ))

    return errors
 
 
def check_us03_birth_before_death(individuals):
    """US03: Birth should occur before death of an individual.
    Not yet implemented.
    """
    errors = []


    
    return errors
 
 
def check_us05_marriage_before_death(individuals, families):
    """US05: Marriage should occur before death of either spouse."""
    errors = []
 
    for family in families.values():
        if family.married_date is None:
            continue
 
        husb = individuals.get(family.husb)
        if husb and husb.death_date and family.married_date >= husb.death_date:
            errors.append((family.married_line,
                f"ERROR: FAMILY: US05: {family.married_line}: {family.id}: "
                f"Married {family.married_date} on or after husband's "
                f"({husb.id}) death on {husb.death_date}"))
 
        wife = individuals.get(family.wife)
        if wife and wife.death_date and family.married_date >= wife.death_date:
            errors.append((family.married_line,
                f"ERROR: FAMILY: US05: {family.married_line}: {family.id}: "
                f"Married {family.married_date} on or after wife's "
                f"({wife.id}) death on {wife.death_date}"))
 
    return errors
 
 
def check_us06_divorce_before_death(individuals, families):
    """US06: Divorce can only occur before death of both spouses."""
    errors = []

    for family in families.values():
        if family.divorced_date is None:
            continue

        husband = individuals.get(family.husb)
        if husband and husband.death_date:
            if family.divorced_date >= husband.death_date:
                errors.append((
                    family.divorced_line,
                    f"ERROR: FAMILY: US06: {family.divorced_line}: {family.id}: "
                    f"Divorce date {family.divorced_date} occurs on or after "
                    f"husband's ({husband.id}) death on {husband.death_date}"
                ))

        wife = individuals.get(family.wife)
        if wife and wife.death_date:
            if family.divorced_date >= wife.death_date:
                errors.append((
                    family.divorced_line,
                    f"ERROR: FAMILY: US06: {family.divorced_line}: {family.id}: "
                    f"Divorce date {family.divorced_date} occurs on or after "
                    f"wife's ({wife.id}) death on {wife.death_date}"
                ))

    return errors
 
 
def check_us07_less_than_150_years_old(individuals, today):
    """US07: Death should be less than 150 years after birth for dead
    people; current date should be less than 150 years after birth
    for living people.
    Not yet implemented.
    """
    errors = []



    return errors



def run_sprint1_checks(individuals, families):
    """Run all Sprint 1 user story checks and print the results,
    sorted by line number so they read in file order."""
 
    today = datetime.date.today()
 
    all_errors = []
    all_errors += check_us01_dates_before_current_date(individuals, families, today)
    all_errors += check_us02_birth_before_marriage(individuals, families)
    all_errors += check_us03_birth_before_death(individuals)
    all_errors += check_us05_marriage_before_death(individuals, families)
    all_errors += check_us06_divorce_before_death(individuals, families)
    all_errors += check_us07_less_than_150_years_old(individuals, today)
 
    all_errors.sort(key=lambda pair: pair[0])
 
    print()
    print("Sprint 1 User Story Results")
    print("-" * 70)
    if not all_errors:
        print("No errors found.")
    else:
        for _, message in all_errors:
            print(message)


# Entry point

def main():
    if len(sys.argv) != 2:
        print("Usage: python gedcom_reader.py <gedcom_file>")
        sys.exit(1)

    filename = sys.argv[1]

    individuals, families = process_gedcom(filename)
    print_individuals(individuals)
    print_families(individuals, families)
    run_sprint1_checks(individuals, families)


if __name__ == "__main__":
    main()
