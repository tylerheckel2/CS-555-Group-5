"""Automated tests for all GEDCOM user stories implemented through Sprint 2.

Run from this folder with: python -m unittest -v test_gedcom
Each test verifies the exact records that should be flagged by one user story.
"""

import contextlib
import datetime
import io
from pathlib import Path
import unittest

import gedcom_reader as gedcom


TEST_FILE = Path(__file__).with_name("sprint2_test.ged")
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
        self.assert_story_errors("US16", errors, ["JB16F1"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
