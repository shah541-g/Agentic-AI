
import unittest

from extractor import extract_emails, is_valid_email
from normalizer import build_contacts, get_domain, normalize_email


class TestEmailExtractor(unittest.TestCase):

    def test_extract_basic_email(self):
        self.assertEqual(
            extract_emails("Contact ali@gmail.com"),
            ["ali@gmail.com"],
        )

    def test_extract_plus_alias(self):
        self.assertEqual(
            extract_emails("sara+jobs@gmail.com"),
            ["sara+jobs@gmail.com"],
        )

    def test_extract_subdomain(self):
        self.assertEqual(
            extract_emails("hr@mail.company.co.uk"),
            ["hr@mail.company.co.uk"],
        )

    def test_extract_multiple_emails(self):
        self.assertEqual(
            extract_emails("ali@gmail.com and sara@example.com"),
            ["ali@gmail.com", "sara@example.com"],
        )

    def test_ignore_malformed_emails(self):
        self.assertEqual(extract_emails("broken@@gmail.com"), [])
        self.assertEqual(extract_emails("missing-domain@"), [])
        self.assertEqual(extract_emails("@example.com"), [])

    def test_ignore_non_string_input(self):
        self.assertEqual(extract_emails(None), [])
        self.assertEqual(extract_emails(""), [])

    
    def test_normalize_domain_case(self):
        self.assertEqual(
            normalize_email("Ali@GMAIL.COM"),
            "ali@gmail.com"
        )


    def test_get_domain(self):
        self.assertEqual(
            get_domain("user@mail.company.co.uk"),
            "mail.company.co.uk",
        )

    def test_validity_check(self):
        self.assertTrue(is_valid_email("ali+jobs@gmail.com"))
        self.assertFalse(is_valid_email("broken@@gmail.com"))

    def test_deduplicate_across_records(self):
        records = [
            {
                "id": "1",
                "sender": "Ali <ali@gmail.com>",
                "body": "Contact ali@gmail.com",
            },
            {
                "id": "2",
                "sender": "ALI <ALI@GMAIL.COM>",
                "body": "",
            },
        ]

        contacts, total_matches, invalid_count = build_contacts(records)

        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts["ali@gmail.com"].occurrences, 2)
        self.assertEqual(
            contacts["ali@gmail.com"].sources,
            {"sender", "body"},
        )
        self.assertEqual(total_matches, 3)
        self.assertEqual(invalid_count, 0)


if __name__ == "__main__":
    unittest.main()
