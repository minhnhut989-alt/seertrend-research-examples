import unittest
from decimal import Decimal

from point_in_time import Vintage, select_as_of, timestamp


def row(value="100", published="09:00:00", received="09:00:02", series="DEMO"):
    return Vintage.from_row({
        "series": series, "period": "2026-01", "value": value,
        "published_at": f"2026-02-05T{published}Z",
        "received_at": f"2026-02-05T{received}Z",
    })


class PointInTimeTests(unittest.TestCase):
    def test_publication_is_not_receipt(self):
        self.assertEqual(select_as_of([row()], "2026-02-05T09:00:01Z"), {})

    def test_exact_receipt_boundary_and_offset(self):
        result = select_as_of([row()], "2026-02-05T16:00:02+07:00")
        self.assertEqual(result[("DEMO", "2026-01")].value, Decimal("100"))

    def test_later_revision_does_not_leak(self):
        records = [row(), row("105", "10:00:00", "10:00:03")]
        before = select_as_of(records, "2026-02-05T09:30:00Z")
        after = select_as_of(records, "2026-02-05T10:00:03Z")
        self.assertEqual(before[("DEMO", "2026-01")].value, 100)
        self.assertEqual(after[("DEMO", "2026-01")].value, 105)

    def test_late_older_release_does_not_replace_revision(self):
        records = [row("105", "10:00:00", "10:00:03"),
                   row("100", "09:00:00", "11:00:00")]
        result = select_as_of(records, "2026-02-05T11:00:00Z")
        self.assertEqual(result[("DEMO", "2026-01")].value, 105)
        self.assertEqual(result, select_as_of(list(reversed(records)),
                                             "2026-02-05T11:00:00Z"))

    def test_publication_gate_even_if_receipt_clock_is_earlier(self):
        self.assertEqual(select_as_of([row(published="10:00:00")],
                                      "2026-02-05T09:30:00Z"), {})

    def test_groups_are_independent(self):
        result = select_as_of([row(), row("2.4", series="OTHER")],
                              "2026-02-05T09:30:00Z")
        self.assertEqual(len(result), 2)

    def test_ambiguous_source_vintage_rejected(self):
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            select_as_of([row(), row("101")], "2026-02-05T09:30:00Z")

    def test_naive_time_and_nonfinite_value_rejected(self):
        with self.assertRaises(ValueError):
            timestamp("2026-02-05T09:00:00")
        with self.assertRaises(ValueError):
            row("NaN")


if __name__ == "__main__":
    unittest.main()
