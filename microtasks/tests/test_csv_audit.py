import unittest

from csv_audit import audit_csv


class CsvAuditTests(unittest.TestCase):
    def test_deduplicates_and_reports_exact_rows(self):
        source = (
            "order_id,email,amount\n"
            "1001,a@example.com,9.50\n"
            "1002,b@example.com,\n"
            "1001,a@example.com,9.50\n"
            ",c@example.com,4.00\n"
        )

        report, cleaned = audit_csv(source, "order_id")

        self.assertEqual(report["counts"]["rows_read"], 4)
        self.assertEqual(report["counts"]["rows_written"], 3)
        self.assertEqual(report["counts"]["duplicates_removed"], 1)
        self.assertEqual(report["duplicates"][0]["row"], 4)
        self.assertEqual(report["duplicates"][0]["first_seen_row"], 2)
        self.assertEqual(report["missing_key_rows"], [5])
        self.assertIn("1002,b@example.com,\n", cleaned)

    def test_rejects_missing_key_column(self):
        with self.assertRaisesRegex(ValueError, "not present"):
            audit_csv("id,name\n1,Ada\n", "order_id")

    def test_rejects_missing_header(self):
        with self.assertRaisesRegex(ValueError, "header"):
            audit_csv("", "id")


if __name__ == "__main__":
    unittest.main()
