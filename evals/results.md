# Extraction eval results

Run 2026-10-11T04:36:10+00:00 against `http://localhost:8000`, model `gpt-4o-mini`, 15 synthetic cases (6 scored fields each). Errors: 0.

## Summary

| Metric | Result |
|---|---|
| Injury type | 15/15 (100.0%) |
| Incident date | 15/15 (100.0%) |
| Insurer | 15/15 (100.0%) |
| Policy limit | 15/15 (100.0%) |
| Claimed damages | 12/15 (80.0%) |
| Liability indicators | 11/15 (73.3%) |
| **Overall field accuracy** | **83/90 (92.2%)** |
| Grounding rate (source quotes found verbatim) | 80/82 (97.6%) |
| PII leaks, document only | 2 of 60 planted (recall 96.7%) |
| PII leaks, with intake-form name (production path) | 0 of 60 planted (recall 100.0%) |

## Per case

| Case | Scenario | Injury | Date | Insurer | Limit | Damages | Liability | Grounded | PII leaks (doc / with name) |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| case_01 | whiplash / rear_end / insurance=full / damages=total / date=iso / layout=police+medical | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 5/5 | 0 / 0 |
| case_02 | fracture_wrist / red_light / insurance=full / damages=total / date=long / layout=police+medical | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/7 | 0 / 0 |
| case_03 | concussion / dui / insurance=insurer only / damages=itemized / date=dmy / layout=police+medical | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | 6/6 | 0 / 0 |
| case_04 | herniated_disc / claimant_cited / insurance=full / damages=total / date=iso / layout=police+medical | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 | 0 / 0 |
| case_05 | sprain_lumbar / conflicting / insurance=none / damages=itemized / date=long / layout=police+medical | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 4/5 | 0 / 0 |
| case_06 | whiplash / no_seatbelt / insurance=full / damages=None / date=iso / layout=police | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 | 0 / 0 |
| case_07 | fracture_tibia / speeding / insurance=insurer only / damages=total / date=dmy / layout=police+medical | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 | 0 / 0 |
| case_08 | tbi / red_light / insurance=full / damages=prose / date=prose / layout=letter | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/7 | 0 / 0 |
| case_09 | sprain_ankle / slip_wet_floor / insurance=full / damages=itemized / date=iso / layout=premises+medical | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/8 | 0 / 0 |
| case_10 | herniated_disc / rear_end / insurance=none / damages=total / date=long / layout=police+medical | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 | 0 / 0 |
| case_11 | whiplash / none / insurance=none / damages=total / date=iso / layout=medical | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 3/3 | 0 / 0 |
| case_12 | concussion / conflicting / insurance=insurer only / damages=None / date=dmy / layout=police / name in prose | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 5/5 | 1 / 0 |
| case_13 | fracture_clavicle / dui / insurance=full / damages=itemized / date=prose / layout=statement+medical | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 | 0 / 0 |
| case_14 | sprain_ankle / claimant_following / insurance=full / damages=total / date=iso / layout=police+medical | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 6/6 | 0 / 0 |
| case_15 | herniated_disc / slip_icy_steps / insurance=insurer only / damages=itemized / date=dmy / layout=premises+medical / name in prose | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 5/5 | 1 / 0 |

## Failures

| Case | Field | Extracted | Expected |
|---|---|---|---|
| case_01 | Liability indicators | [Driver 2 looked down at his phone] | must mention: rear/from behind/struck it from behind |
| case_03 | Claimed damages | 6180 | 6280 |
| case_05 | Claimed damages | 3780 | 5780 |
| case_05 | Liability indicators | [Vehicle 1 entered the intersection on a stale amber light; Vehicle 2 ran the red light] | must mention: witness/conflict/disputed/unclear |
| case_12 | Liability indicators | [Vehicle 1 entered the intersection on a stale amber light; Vehicle 2 ran the red light] | must mention: witness/conflict/disputed/unclear |
| case_15 | Claimed damages | 4920 | 5820 |
| case_15 | Liability indicators | [steps not salted or cleared despite freezing rain warning] | must mention: ice/icy; salt/cleared/not been salted |

## Ungrounded source quotes

- case_05: claimed_damages
- case_09: claimed_damages

## PII that survived redaction

- case_12: document only: 1 (name); with form name: 0
- case_15: document only: 1 (name); with form name: 0

## Failure analysis

Written after reviewing the run above. Labels for every failure were re-checked by hand and are correct.

**1. The model cannot reliably add up itemized bills.** Every case with a printed total or a total stated in prose was extracted exactly. Every case with itemized lines and no total (cases 03, 05, 09, 13, 15) came back with the wrong sum, off by $40 to $2,000. Two of those (09: $4,355 vs $4,395; 13: $21,000 vs $21,180) are within the 1% tolerance and count as correct, so the 12/15 damages score overstates arithmetic accuracy: under exact matching it would be 10/15. In cases 05 and 09 the model also invented a "Total" line that does not exist in the document. The grounding check flagged both, which is why grounding is 80/82 rather than 82/82. **Fix direction:** have the model return line items with their quotes and compute the sum in code, rather than trusting model arithmetic.

**2. Disputed liability is flattened into facts.** In both conflicting-witness cases (05, 12) the model listed each witness's claim as a plain fact ("Vehicle 2 ran the red light") and dropped the fact that the accounts conflict. This is the most consequential error: a keyword rule downstream would read "ran the red light" as favorable liability on a case that is actually disputed. **Fix direction:** ask for an explicit `disputed` flag or attribution ("per Witness 2") on each indicator.

**3. Incomplete liability lists.** Case 01 returned only "Driver 2 looked down at his phone" and omitted the rear-end collision itself. Case 15 returned "steps not salted or cleared" but not the ice. Both outputs are true; they are scored wrong because a key concept is missing. These are partly a strictness choice in the labels, but a rear-end impact is the main liability fact in case 01, so the miss is real.

**4. PII redaction misses unlabeled names, as designed.** The two leaks in the document-only check are the claimant's full name written in narrative prose (cases 12, 15), where no label, title or known name is present. In the production path the intake form supplies the claimant's name, and both leaks disappear (0/60). Other people named in prose without a title (witnesses, neighbours) would still leak; that is a known limitation of regex redaction.

**What held up:** injury type, incident date (including `dd/mm/yyyy`, long-form and prose-only dates, and the 2023 case), insurer and policy limit were 15/15 each, including the insurer-only, no-insurance and prose-only variants.

Caveat: 15 cases is a small sample, and these are template-generated, so the documents are cleaner than real police reports and medical bills.
