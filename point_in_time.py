"""Select the latest published data vintage actually received by a cutoff.

Educational example. No network calls, broker connections or order execution.
Python 3.11+; standard library only.
"""

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import sys


def timestamp(text):
    value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Every timestamp needs an explicit timezone")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class Vintage:
    series: str
    period: str
    value: Decimal
    published_at: datetime
    received_at: datetime

    @property
    def available_at(self):
        return max(self.published_at, self.received_at)

    @classmethod
    def from_row(cls, row):
        if not row["series"].strip() or not row["period"].strip():
            raise ValueError("series and period cannot be empty")
        value = Decimal(row["value"])
        if not value.is_finite():
            raise ValueError("value must be finite")
        return cls(row["series"].strip(), row["period"].strip(), value,
                   timestamp(row["published_at"]), timestamp(row["received_at"]))


def select_as_of(vintages, decision_at):
    """Return one vintage per (series, period), with equality allowed at cutoff.

    Publication time orders source revisions; receipt time gates availability.
    A late delivery of an older release must not replace a newer revision.
    Conflicting values with the same source timestamp are rejected.
    """
    cutoff = timestamp(decision_at)
    selected, seen = {}, {}
    for vintage in vintages:
        if vintage.available_at > cutoff:
            continue
        key = (vintage.series, vintage.period)
        identity = (*key, vintage.published_at)
        if identity in seen and seen[identity] != vintage.value:
            raise ValueError("Conflicting values share a source timestamp")
        seen[identity] = vintage.value
        prior = selected.get(key)
        if prior is None or (vintage.published_at, vintage.received_at) > (
                prior.published_at, prior.received_at):
            selected[key] = vintage
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", help="Input CSV; never modified")
    parser.add_argument("--at", required=True, help="Decision cutoff with timezone")
    args = parser.parse_args()
    try:
        with open(args.csv_path, newline="", encoding="utf-8-sig") as source:
            rows = [Vintage.from_row(row) for row in csv.DictReader(source)]
        selected = select_as_of(rows, args.at)
    except (ValueError, InvalidOperation, KeyError, TypeError, OSError) as error:
        parser.error(str(error))
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["series", "period", "value", "published_at", "received_at",
                     "available_at"])
    for key in sorted(selected):
        row = selected[key]
        writer.writerow([row.series, row.period, row.value,
                         row.published_at.isoformat(), row.received_at.isoformat(),
                         row.available_at.isoformat()])


if __name__ == "__main__":
    main()
