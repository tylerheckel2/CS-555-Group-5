"""
CS 555 - Agile Methods for Software Development Group 5 Assignment
GEDCOM Project - Sprint 3

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
import calendar

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


def add_months(date, months):
    """Return the date "months" months after "date", clamping the day
    if the target month is shorter (e.g. 31 Jan + 1 month -> 28/29 Feb)."""
    month_index = date.month - 1 + months
    year = date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(date.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)

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
        self.sex_line = None
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
                        current_indi.sex_line = line_no
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
    """ US03: Birth should occur before death of an individual."""
    errors = []
    
    for person in individuals.values():
        if person.birth_date is None or person.death_date is None:
            continue
 
        if person.death_date < person.birth_date:
            errors.append((
                person.death_line,
                f"ERROR: INDIVIDUAL: US03: {person.death_line}: {person.id}: "
                f"Died {person.death_date} before born {person.birth_date}"
            ))
 
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
    for living people."""
    errors = []
 
    for person in individuals.values():
        if person.birth_date is None:
            continue
 
        if person.death_date:
            age = calculate_age(person.birth_date, person.death_date)
            if age >= 150:
                errors.append((
                    person.birth_line,
                    f"ERROR: INDIVIDUAL: US07: {person.birth_line}: {person.id}: "
                    f"More than 150 years old at death - Birth {person.birth_date}: "
                    f"Death {person.death_date}"
                ))
        elif person.alive:
            age = calculate_age(person.birth_date, today)
            if age >= 150:
                errors.append((
                    person.birth_line,
                    f"ERROR: INDIVIDUAL: US07: {person.birth_line}: {person.id}: "
                    f"More than 150 years old - Birth date {person.birth_date}"
                ))
 
    return errors


# Sprint 2 user story checks

def check_us09_birth_before_death_of_parents(individuals, families):
    """US09: Child should be born before death of mother, and before
    9 months after death of father."""
    errors = []

    for family in families.values():
        mother = individuals.get(family.wife)
        father = individuals.get(family.husb)

        for child_id in family.chil:
            child = individuals.get(child_id)
            if child is None or child.birth_date is None:
                continue

            if mother and mother.death_date and child.birth_date >= mother.death_date:
                errors.append((
                    child.birth_line,
                    f"ERROR: FAMILY: US09: {child.birth_line}: {family.id}: "
                    f"Child ({child.id}) born {child.birth_date} on or after "
                    f"mother's ({mother.id}) death on {mother.death_date}"
                ))

            if father and father.death_date:
                latest_allowed = add_months(father.death_date, 9)
                if child.birth_date > latest_allowed:
                    errors.append((
                        child.birth_line,
                        f"ERROR: FAMILY: US09: {child.birth_line}: {family.id}: "
                        f"Child ({child.id}) born {child.birth_date} more than "
                        f"9 months after father's ({father.id}) death on "
                        f"{father.death_date}"
                    ))

    return errors


def check_us10_marriage_after_14(individuals, families):
    """US10: Marriage should be at least 14 years after both spouses' birth."""
    errors = []

    for family in families.values():
        if family.married_date is None:
            continue

        husband = individuals.get(family.husb)
        if husband and husband.birth_date:
            age = calculate_age(husband.birth_date, family.married_date)
            if age < 14:
                errors.append((
                    family.married_line,
                    f"ERROR: FAMILY: US10: {family.married_line}: {family.id}: "
                    f"Husband ({husband.id}) born {husband.birth_date} was {age} "
                    f"years old at marriage on {family.married_date}, younger than 14"
                ))

        wife = individuals.get(family.wife)
        if wife and wife.birth_date:
            age = calculate_age(wife.birth_date, family.married_date)
            if age < 14:
                errors.append((
                    family.married_line,
                    f"ERROR: FAMILY: US10: {family.married_line}: {family.id}: "
                    f"Wife ({wife.id}) born {wife.birth_date} was {age} "
                    f"years old at marriage on {family.married_date}, younger than 14"
                ))

    return errors


def check_us11_no_bigamy(individuals, families):
    """US11: Marriage should not occur while either spouse is already
    married to someone else."""
    errors = []

    for person in individuals.values():
        marriages = []

        for family in families.values():
            if family.husb == person.id or family.wife == person.id:
                if family.married_date:
                    marriages.append(family)

        marriages.sort(key=lambda fam: fam.married_date)

        for i in range(len(marriages) - 1):
            first_family = marriages[i]
            second_family = marriages[i + 1]

            end_date = first_family.divorced_date

            if first_family.husb == person.id:
                spouse_id = first_family.wife
            else:
                spouse_id = first_family.husb

            spouse = individuals.get(spouse_id)

            if spouse and spouse.death_date:
                if end_date is None or spouse.death_date < end_date:
                    end_date = spouse.death_date

            if end_date is None or second_family.married_date < end_date:
                errors.append((
                    second_family.married_line,
                    f"ERROR: INDIVIDUAL: US11: {second_family.married_line}: "
                    f"{person.id}: Bigamy detected - marriage in "
                    f"{second_family.id} occurred before previous marriage ended"
                ))

    return errors

def check_us12_parents_not_too_old(individuals, families):
    """US12: Mother should be less than 60 years older than her children
    and father should be less than 80 years older than his children."""
    errors = []

    for family in families.values():
        mother = individuals.get(family.wife)
        father = individuals.get(family.husb)

        for child_id in family.chil:
            child = individuals.get(child_id)
            if child is None or child.birth_date is None:
                continue

            if mother and mother.birth_date:
                mother_age_diff = calculate_age(mother.birth_date, child.birth_date)
                if mother_age_diff is not None and mother_age_diff >= 60:
                    errors.append((
                        child.birth_line,
                        f"ERROR: FAMILY: US12: {child.birth_line}: {family.id}: "
                        f"Mother ({mother.id}) born {mother.birth_date} is {mother_age_diff} "
                        f"years older than child ({child.id}) born {child.birth_date} (>= 60)"
                    ))

            if father and father.birth_date:
                father_age_diff = calculate_age(father.birth_date, child.birth_date)
                if father_age_diff is not None and father_age_diff >= 80:
                    errors.append((
                        child.birth_line,
                        f"ERROR: FAMILY: US12: {child.birth_line}: {family.id}: "
                        f"Father ({father.id}) born {father.birth_date} is {father_age_diff} "
                        f"years older than child ({child.id}) born {child.birth_date} (>= 80)"
                    ))

    return errors


def check_us13_siblings_spacing(individuals, families):
    """US13: Birth dates of siblings should be more than 8 months
    apart, or less than 2 days apart (to allow for twins)."""
    errors = []

    for family in families.values():
        siblings = [individuals[cid] for cid in family.chil
                    if cid in individuals and individuals[cid].birth_date]

        for i in range(len(siblings)):
            for j in range(i + 1, len(siblings)):
                a, b = siblings[i], siblings[j]
                earlier, later = (a, b) if a.birth_date <= b.birth_date else (b, a)

                gap_days = (later.birth_date - earlier.birth_date).days
                min_spacing_date = add_months(earlier.birth_date, 8)

                is_twins = gap_days < 2
                is_spaced_out = later.birth_date >= min_spacing_date

                if not is_twins and not is_spaced_out:
                    errors.append((
                        later.birth_line,
                        f"ERROR: FAMILY: US13: {later.birth_line}: {family.id}: "
                        f"Siblings ({earlier.id}) born {earlier.birth_date} and "
                        f"({later.id}) born {later.birth_date} are only "
                        f"{gap_days} days apart"
                    ))

    return errors


def check_us14_multiple_births_le_5(individuals, families):
    """US14: No more than 5 siblings should be born at the same time
    (multiple birth). Siblings born less than 2 days apart count as the
    same birth, matching the twins rule in US13."""
    errors = []

    for family in families.values():
        siblings = [individuals[cid] for cid in family.chil
                    if cid in individuals and individuals[cid].birth_date]
        siblings.sort(key=lambda person: person.birth_date)

        i = 0
        while i < len(siblings):
            first = siblings[i]
            same_birth = [first]

            j = i + 1
            while j < len(siblings) and (siblings[j].birth_date - first.birth_date).days < 2:
                same_birth.append(siblings[j])
                j += 1

            if len(same_birth) > 5:
                last = same_birth[-1]
                errors.append((
                    last.birth_line,
                    f"ERROR: FAMILY: US14: {last.birth_line}: {family.id}: "
                    f"{len(same_birth)} siblings born at the same time on "
                    f"{first.birth_date}, more than 5"
                ))

            i = j

    return errors

def check_us15_fewer_than_15_siblings(families):
    """US15: There should be fewer than 15 siblings in a family."""
    errors = []

    for family in families.values():
        number_of_children = len(family.chil)

        if number_of_children >= 15:
            errors.append((
                family.line_no,
                f"ERROR: FAMILY: US15: {family.line_no}: {family.id}: "
                f"Family has {number_of_children} children, which is not fewer than 15"
            ))

    return errors


def extract_last_name(name):
    """Return the surname inside '/' delimiters, or empty string if missing."""
    parts = name.split("/")
    return parts[1].strip() if len(parts) >= 2 else ""


def check_us16_male_last_names(individuals, families):
    """US16: All male members of a family should have the same last name."""
    errors = []

    for family in families.values():
        father = individuals.get(family.husb)
        if father is None or not father.name:
            continue

        family_last_name = extract_last_name(father.name)
        if not family_last_name:
            continue

        for child_id in family.chil:
            child = individuals.get(child_id)
            if child and child.sex == "M" and child.name:
                child_last_name = extract_last_name(child.name)
                if child_last_name and child_last_name != family_last_name:
                    errors.append((
                        child.line_no,
                        f"ERROR: FAMILY: US16: {child.line_no}: {family.id}: "
                        f"Male child ({child.id}, '{child.name}') has a different "
                        f"last name than father ({father.id}, '{father.name}')"
                    ))

    return errors

# Sprint 3 user story checks

def check_us17_no_marriages_to_descendants(individuals, families):
    """US17: Parents should not marry any of their descendants."""
    errors = []

    # Everyone's children, across every family they are a parent in
    children_of = {}
    for family in families.values():
        for parent_id in (family.husb, family.wife):
            if parent_id:
                children_of.setdefault(parent_id, set()).update(family.chil)

    def descendants_of(person_id):
        # Children, grandchildren, and so on. The found set also keeps
        # this from looping forever if the file has circular data.
        found = set()
        to_visit = list(children_of.get(person_id, ()))
        while to_visit:
            current = to_visit.pop()
            if current in found:
                continue
            found.add(current)
            to_visit.extend(children_of.get(current, ()))
        return found

    for family in families.values():
        if not family.husb or not family.wife:
            continue

        line_no = family.married_line or family.line_no

        if family.wife in descendants_of(family.husb):
            errors.append((
                line_no,
                f"ERROR: FAMILY: US17: {line_no}: {family.id}: "
                f"Husband ({family.husb}) is married to his descendant, "
                f"wife ({family.wife})"
            ))

        if family.husb in descendants_of(family.wife):
            errors.append((
                line_no,
                f"ERROR: FAMILY: US17: {line_no}: {family.id}: "
                f"Wife ({family.wife}) is married to her descendant, "
                f"husband ({family.husb})"
            ))

    return errors


def check_us21_correct_gender_for_role(individuals, families):
    """US21: Husband in family should be male and wife in family should be
    female. People with no SEX record are skipped (nothing to compare)."""
    errors = []

    for family in families.values():
        husband = individuals.get(family.husb)
        if husband and husband.sex and husband.sex != "M":
            line_no = husband.sex_line or husband.line_no
            errors.append((
                line_no,
                f"ERROR: FAMILY: US21: {line_no}: {family.id}: "
                f"Husband ({husband.id}) should be male but is listed as {husband.sex}"
            ))

        wife = individuals.get(family.wife)
        if wife and wife.sex and wife.sex != "F":
            line_no = wife.sex_line or wife.line_no
            errors.append((
                line_no,
                f"ERROR: FAMILY: US21: {line_no}: {family.id}: "
                f"Wife ({wife.id}) should be female but is listed as {wife.sex}"
            ))

    return errors

def check_us19_first_cousins_should_not_marry(individuals, families):
    """US19: First cousins should not marry."""
    errors = []

    # Find each person's parents using the family records
    parents = {}

    for family in families.values():
        for child_id in family.chil:
            parents.setdefault(child_id, set()).update(
                parent_id
                for parent_id in (family.husb, family.wife)
                if parent_id in individuals
            )

    # Two people are siblings if they share a parent
    def are_siblings(person1_id, person2_id):
        return bool(
            parents.get(person1_id, set())
            & parents.get(person2_id, set())
        )

    for family in families.values():
        husband_parents = parents.get(family.husb, set())
        wife_parents = parents.get(family.wife, set())

        first_cousins = any(
            are_siblings(husband_parent, wife_parent)
            for husband_parent in husband_parents
            for wife_parent in wife_parents
        )

        if first_cousins:
            errors.append((
                family.married_line or family.line_no,
                f"ERROR: FAMILY: US19: "
                f"{family.married_line or family.line_no}: {family.id}: "
                f"Husband ({family.husb}) and wife ({family.wife}) "
                f"are first cousins"
            ))

    return errors
 
def check_us23_unique_name_and_birth_date(individuals):
    """US23: Individuals should have unique names and birth dates."""
    errors = []
    seen = {}

    for person in individuals.values():
        if not person.name or person.birth_date is None:
            continue

        key = (person.name.strip(), person.birth_date)

        if key in seen:
            original = seen[key]
            line_no = person.birth_line or person.line_no

            errors.append((
                line_no,
                f"ERROR: INDIVIDUAL: US23: {line_no}: {person.id}: "
                f"Same name ({person.name}) and birth date "
                f"({person.birth_date}) as individual ({original.id})"
            ))
        else:
            seen[key] = person

    return errors
  
def run_all_checks(individuals, families):
    """Run every user story check implemented so far (Sprint 1 and
    Sprint 2) and print the results together, sorted by line number
    so they read in file order."""

    today = datetime.date.today()

    all_errors = []
    # Sprint 1
    all_errors += check_us01_dates_before_current_date(individuals, families, today)
    all_errors += check_us02_birth_before_marriage(individuals, families)
    all_errors += check_us03_birth_before_death(individuals)
    all_errors += check_us05_marriage_before_death(individuals, families)
    all_errors += check_us06_divorce_before_death(individuals, families)
    all_errors += check_us07_less_than_150_years_old(individuals, today)
    # Sprint 2
    all_errors += check_us09_birth_before_death_of_parents(individuals, families)
    all_errors += check_us10_marriage_after_14(individuals, families)
    all_errors += check_us11_no_bigamy(individuals, families)
    all_errors += check_us12_parents_not_too_old(individuals, families)
    all_errors += check_us13_siblings_spacing(individuals, families)
    all_errors += check_us14_multiple_births_le_5(individuals, families)
    all_errors += check_us15_fewer_than_15_siblings(families)
    all_errors += check_us16_male_last_names(individuals, families)
    all_errors += check_us17_no_marriages_to_descendants(individuals, families)
    all_errors += check_us19_first_cousins_should_not_marry(individuals, families)
    all_errors += check_us21_correct_gender_for_role(individuals, families)
    all_errors += check_us23_unique_name_and_birth_date(individuals)

    all_errors.sort(key=lambda pair: pair[0])

    print()
    print("User Story Results (Sprint 1 + Sprint 2 + Sprint 3)")
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
    run_all_checks(individuals, families)


if __name__ == "__main__":
    main()
