### Real Estate Data Quality

The `Real_Estate_(Current_Assessments).csv` source file contains 15,703 rows.

During database import, a duplicate primary-key error was detected for:

- ParcelNumber: `550073110`
- OBJECTID: `9465`
- Address: `1412 SHORT 18TH ST`
- CurrentAssessedValue: `$552,100`

Inspection confirmed that the two records were identical across all columns.

A cleaned copy of the dataset was created without modifying the original source file.

- Original rows: 15,703
- Exact duplicate rows removed: 1
- Final imported rows: 15,702
- Duplicate rate: ~0.0064%

`ParcelNumber` remains the primary key because the only duplicate parcel record was an exact duplicate row rather than a distinct property record.

# Checkpoint 9 — Dataset Import & Profiling Baseline

## Purpose

Checkpoint 9 introduced the current real-estate assessment dataset and
crime dataset into PostgreSQL.

This checkpoint establishes the baseline data-quality and street-matching
metrics before street-name normalization is implemented in Checkpoint 10.

---

## Real Estate Dataset

Source: `Real_Estate_(Current_Assessments).csv`

### Import

- Raw source rows: 15,703
- Exact duplicate rows detected: 1
- Final imported rows: 15,702
- Unique parcel numbers: 15,702
- Unique OBJECTIDs: 15,702
- Unique street names: 592

### Duplicate Detected

The source dataset contained one exact duplicate:

- ParcelNumber: `550073110`
- OBJECTID: `9465`
- Address: `1412 SHORT 18TH ST`
- CurrentAssessedValue: `$552,100`

The two records were identical across all columns.

The original source file was preserved and a cleaned copy was created
for database import.

Duplicate rate:

1 / 15,703 = ~0.0064%

### Missing Data

- Missing street numbers: 19
- Missing street names: 0
- Missing unit numbers: 13,792

### Assessment Values

- Minimum: $0
- Average: $974,635
- Maximum: $820,901,600

The large maximum value indicates that average assessed value should not
automatically be interpreted as the value of a typical residential property.

---

## Crime Dataset

Source: `Crime_Data.csv`

### Import

- Imported rows: 26,418
- Unique RecordIDs: 26,418
- Unique IncidentIDs: 26,418
- Unique raw street-name values: 4,043
- Unique offense types: 108

### Missing Data

- Missing block numbers: 2,044
- Missing street names: 0

### Date Coverage

- Earliest report: April 23, 2021
- Latest report: April 20, 2026

---

## Street Matching Baseline

The baseline intentionally uses exact string equality:

`real_estate_current_assessment.st_name = crime.street_name`

No street-name normalization is applied at this stage.

### Results

- Real-estate street names: 592
- Exact matching real-estate street names: 519
- Unmatched real-estate street names: 73

Street-name match rate:

519 / 592 = 87.67%

### Property Coverage

- Total properties: 15,702
- Properties on exactly matched streets: 15,174
- Properties without an exact street match: 528

Property coverage:

15,174 / 15,702 = 96.64%

Although 12.33% of unique real-estate street names fail the exact match,
those streets contain only 3.36% of the imported properties.

---

## Database Security

The application database role `ai_reader` was tested against both new
tables.

Permissions:

| Table | SELECT | INSERT | UPDATE | DELETE |
|---|---|---|---|---|
| real_estate_current_assessment | Allowed | Denied | Denied | Denied |
| crime | Allowed | Denied | Denied | Denied |

This ensures that AI tools can query the datasets without modifying
source data.

---

## Checkpoint 10 Comparison Target

Checkpoint 10 will introduce street-name normalization.

The main baseline metrics to improve are:

- Exact street-name match rate: **87.67%**
- Property coverage: **96.64%**

Checkpoint 10 should compare normalized matching against these values
rather than replacing the baseline.