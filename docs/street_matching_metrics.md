# Street Matching Metrics

This document records the street-matching performance before and after
improving the street normalization logic.

## Before Normalization Improvements

Crime streets:
- Total: 592
- Matched: 532
- Unmatched: 60
- Match rate: 89.86%

Properties:
- Total: 15,702
- Matched: 15,315
- Unmatched: 387
- Coverage: 97.54%

## After Normalization Improvements

Crime streets:
- Total: 592
- Matched: 544
- Unmatched: 48
- Match rate: 91.89%

Properties:
- Total: 15,702
- Matched: 15,431
- Unmatched: 271
- Coverage: 98.27%

## Improvement

- Crime street match rate: 89.86% → 91.89% (+2.03 percentage points)
- Matched crime streets: 532 → 544 (+12)
- Property coverage: 97.54% → 98.27% (+0.73 percentage points)
- Matched properties: 15,315 → 15,431 (+116)
- Unmatched properties: 387 → 271 (-116)