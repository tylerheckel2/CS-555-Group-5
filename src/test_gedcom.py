"""Automated tests for all GEDCOM user stories implemented through Sprint 4.

Run from this folder with: python -m unittest -v test_gedcom
Each test verifies the exact records that should be flagged by one user story.
"""

import contextlib
import datetime
import io
import os
from pathlib import Path
import tempfile
import unittest

import gedcom_reader as gedcom


TEST_FILE = Path(__file__).with_name("sprint4_test.ged")
TEST_DATE = datetime.date(2026, 10, 12)


class TestGEDCOMUserStories(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The GEDCOM parser prints a trace; tests only need the parsed records.
        with contextlib.redirect_stdout(io.StringIO()):
            cls.individuals, cls.families = gedcom.process_gedcom(str(TEST_FILE))

    def assert_story_errors(self, story, errors, expected_ids):
        # Check which exact individual/family IDs each rule flags.
        # Requiring an exact match also catches extra, incorrect violations.
        actual_ids = []
        for line, message in errors:
            self.assertIsInstance(line, int)
            self.assertIn(f": {story}: ", message)
            actual_ids.append(message.split(": ", 5)[4])
        self.assertEqual(sorted(actual_ids), sorted(expected_ids))

    # Sprint 1
    def test_us01_dates_before_current_date(self):
        errors = gedcom.check_us01_dates_before_current_date(
            self.individuals, self.families, TEST_DATE)
        self.assert_story_errors("US01", errors, ["T1"])

    def test_us02_birth_before_marriage(self):
        errors = gedcom.check_us02_birth_before_marriage(self.individuals, self.families)
        self.assert_story_errors("US02", errors, ["TF1"])

    def test_us03_birth_before_death(self):
        errors = gedcom.check_us03_birth_before_death(self.individuals)
        self.assert_story_errors("US03", errors, ["T2"])

    def test_us05_marriage_before_death(self):
        errors = gedcom.check_us05_marriage_before_death(self.individuals, self.families)
        self.assert_story_errors("US05", errors, ["TF2"])

    def test_us06_divorce_before_death(self):
        errors = gedcom.check_us06_divorce_before_death(self.individuals, self.families)
        self.assert_story_errors("US06", errors, ["TF3"])

    def test_us07_less_than_150_years_old(self):
        errors = gedcom.check_us07_less_than_150_years_old(self.individuals, TEST_DATE)
        self.assert_story_errors("US07", errors, ["T3", "T4"])

    # Sprint 2
    def test_us09_birth_before_death_of_parents(self):
        errors = gedcom.check_us09_birth_before_death_of_parents(self.individuals, self.families)
        self.assert_story_errors("US09", errors, ["TF9", "TF9B"])

    def test_us10_marriage_after_14(self):
        errors = gedcom.check_us10_marriage_after_14(self.individuals, self.families)
        self.assert_story_errors("US10", errors, ["TF1", "TF1", "BQ10F1"])

    def test_us11_no_bigamy(self):
        errors = gedcom.check_us11_no_bigamy(self.individuals, self.families)
        self.assert_story_errors("US11", errors, ["MI11H"])

    def test_us12_parents_not_too_old(self):
        errors = gedcom.check_us12_parents_not_too_old(self.individuals, self.families)
        self.assert_story_errors("US12", errors, ["JB12F1", "JB12F1"])

    def test_us13_siblings_spacing(self):
        errors = gedcom.check_us13_siblings_spacing(self.individuals, self.families)
        self.assert_story_errors("US13", errors, ["TF13"])

    def test_us14_multiple_births_le_5(self):
        errors = gedcom.check_us14_multiple_births_le_5(self.individuals, self.families)
        self.assert_story_errors("US14", errors, ["BQ14F1"])

    def test_us15_fewer_than_15_siblings(self):
        errors = gedcom.check_us15_fewer_than_15_siblings(self.families)
        self.assert_story_errors("US15", errors, ["MI15F"])

    def test_us16_male_last_names(self):
        errors = gedcom.check_us16_male_last_names(self.individuals, self.families)
        self.assert_story_errors("US16", errors, ["JB16F1", "JB20F1"])

    # Sprint 3
    def test_us17_no_marriages_to_descendants(self):
        errors = gedcom.check_us17_no_marriages_to_descendants(self.individuals, self.families)
        self.assert_story_errors("US17", errors, ["TH17AF2", "TH17BF2", "TH17CF3"])

    def test_us21_correct_gender_for_role(self):
        errors = gedcom.check_us21_correct_gender_for_role(self.individuals, self.families)
        self.assert_story_errors("US21", errors, ["TH21F1", "TH21F2", "TH21F3", "TH21F3"])

    def test_us18_siblings_should_not_marry(self):
        errors = gedcom.check_us18_siblings_should_not_marry(self.individuals, self.families)
        self.assert_story_errors("US18", errors, ["BQ18F2"])
    
    def test_us22_unique_ids(self):
        errors = gedcom.check_us22_unique_ids(self.individuals, self.families)
        self.assert_story_errors("US22", errors, ["BQ22W1", "BQ22F1"])

    def test_us19_first_cousins_should_not_marry(self):
        errors = gedcom.check_us19_first_cousins_should_not_marry(
            self.individuals, self.families
        )
        self.assert_story_errors("US19", errors, ["MI19F4"])

    def test_us23_unique_name_and_birth_date(self):
        errors = gedcom.check_us23_unique_name_and_birth_date(
            self.individuals
        )
        self.assert_story_errors("US23", errors, ["JB24H2", "JB24W2", "MI23I2", "TH25C2"])

    def test_us20_aunts_and_uncles(self):
        errors = gedcom.check_us20_aunts_and_uncles(self.individuals, self.families)
        self.assert_story_errors("US20", errors, ["JB20F3"])

    def test_us24_unique_families_by_spouses(self):
        errors = gedcom.check_us24_unique_families_by_spouses(self.individuals, self.families)
        self.assert_story_errors("US24", errors, ["JB24F2"])

    # Sprint 4
    def test_us25_unique_first_names_in_families(self):
        errors = gedcom.check_us25_unique_first_names_in_families(self.individuals, self.families)
        self.assert_story_errors("US25", errors, ["TH25F1"])

    def test_us29_list_deceased(self):
        deceased = gedcom.get_deceased(self.individuals)
        ids = [person.id for person in deceased]
        self.assertEqual(ids, sorted(ids))
        for known_deceased in ("@I1@", "T2", "T4", "TH17AW"):
            self.assertIn(known_deceased, ids)
        for known_living in ("@I2@", "T1", "T3", "TH17AH"):
            self.assertNotIn(known_living, ids)
        self.assertTrue(all(not person.alive for person in deceased))
        self.assertEqual(len(deceased),
                         sum(1 for person in self.individuals.values() if not person.alive))

    def test_us29_printed_list_has_header_and_deceased_people(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            gedcom.print_deceased(self.individuals)
        text = out.getvalue()
        self.assertIn("US29: List of Deceased Individuals", text)
        self.assertIn("Age at Death", text)
        self.assertIn("John /Anderson/", text)
        self.assertNotIn("Mary /Whitfield/", text)
        
    def test_us27_include_individual_ages(self):
        ages = gedcom.get_individual_ages(
            self.individuals, TEST_DATE
        )

        # Living individual
        self.assertEqual(ages["@I6@"], 45)

        # Deceased individual
        self.assertEqual(ages["@I1@"], 33)

        # Missing birth date
        self.assertIsNone(
            gedcom.calculate_age(None, TEST_DATE)
        )

        # Every individual should have an age entry
        self.assertEqual(
            len(ages),
            len(self.individuals)
        )
        
    # US31 - List Living Single (MI)
    def test_us31_list_living_single(self):
        people = gedcom.get_living_single(
            self.individuals, self.families
        )

        ids = [person.id for person in people]

        self.assertEqual(ids, sorted(ids))

        # Positive test
        self.assertIn("MI31_SINGLE", ids)

        # Negative tests
        self.assertNotIn("MI31_MARRIED", ids)
        self.assertNotIn("MI31_DECEASED", ids)
        self.assertNotIn("MI31_YOUNG", ids)

        for person in people:
            self.assertTrue(person.alive)

            age = gedcom.calculate_age(
                person.birth_date,
                datetime.date.today()
            )

            self.assertIsNotNone(age)
            self.assertGreater(age, 30)

            self.assertFalse(any(
                family.married_date is not None
                and person.id in (family.husb, family.wife)
                for family in self.families.values()
            ))



if __name__ == "__main__":
    unittest.main(verbosity=2)
