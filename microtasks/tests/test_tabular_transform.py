import csv
import json
import unittest
from io import StringIO

from tabular_transform import csv_to_records, json_to_csv


class TabularTransformTests(unittest.TestCase):
    def test_csv_to_json_converts_empty_and_numeric_fields(self):
        source = "id,name,amount\n1,Ada,2.50\n2,,\n"

        records = csv_to_records(source, ["amount"])

        self.assertEqual(records[0], {"id": "1", "name": "Ada", "amount": 2.5})
        self.assertEqual(records[1], {"id": "2", "name": None, "amount": None})

    def test_csv_to_json_rejects_invalid_number_with_row(self):
        with self.assertRaisesRegex(ValueError, "row 2.*amount.*not numeric"):
            csv_to_records("id,amount\n1,not-a-number\n", ["amount"])

    def test_json_to_csv_validates_output_and_field_union(self):
        source = json.dumps([{"id": 1, "name": "Ada"}, {"id": 2, "amount": 4.5}])

        rendered, report = json_to_csv(source)
        rows = list(csv.DictReader(StringIO(rendered)))

        self.assertTrue(report["valid_csv"])
        self.assertEqual(report["rows"], 2)
        self.assertEqual(report["fields"], ["id", "name", "amount"])
        self.assertEqual(rows[1], {"id": "2", "name": "", "amount": "4.5"})

    def test_json_to_csv_rejects_nested_values(self):
        with self.assertRaisesRegex(ValueError, "nested value"):
            json_to_csv('[{"id": 1, "meta": {"ok": true}}]')


if __name__ == "__main__":
    unittest.main()
