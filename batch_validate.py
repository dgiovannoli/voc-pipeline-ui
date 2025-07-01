#!/usr/bin/env python3
import csv
from validators.quote_validator import QuoteValidator

def main():
    reader = csv.DictReader(open("stage1_output.csv"))
    v = QuoteValidator()
    validated = []
    for row in reader:
        result = v.validate(row)
        if result:
            validated.append(result)

    # Preserve all original columns + the two new JSON columns
    fieldnames = reader.fieldnames + ["validated_evidence", "quality_report"]
    with open("validated_quotes.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(validated)

if __name__ == "__main__":
    main()
