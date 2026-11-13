# Synthetic 835 / ERA examples, annotated segment by segment

Published by **Jovanie Rosario, Visera / Focus Care LLC**. We make the viewer linked here. These original examples and explanations were prepared with AI assistance and reviewed against the references below.

**Every person, organisation, claim, member, provider, tax, trace and payment identifier in these four files is invented. No real patient or payer remittance was used.** All interchanges carry the ISA15 test flag `T`. Never send these files to a payer, bank, clearinghouse production endpoint or clinical system.

This is a small reading and parser-development aid, not a certified implementation guide, a claim-submission fixture, a complete 005010X221A1 conformance suite or proof that a parser handles arbitrary ERAs. The examples intentionally omit many situational loops and use fake identifiers. Production work needs the applicable licensed implementation guide and trading-partner companion guide.

## Start here

1. Download a file from `samples/` and inspect it in a local text editor.
2. Follow its numbered table below. Each file has one interchange, one group and one 835.
3. Run `python validate_examples.py` using Python 3.10 or newer. It needs only the standard library.
4. For an optional visual comparison, use the [free Visera viewer](https://viseraapp.com/viewer?utm_source=github-samples&utm_medium=referral&utm_campaign=growth-20261113) with one of these invented files or its built-in synthetic sample. It works without an account. No export, storage or data-handling assurance is implied.

An 835 is remittance data; changing its extension to PDF or CSV does not convert it. The figures below are expectations for these teaching files, not a claim about any viewer's displayed totals.

## Shapes and expected amounts

Amounts are USD for this exercise. `manifest.json` is the machine-readable expected result.

| File | Claims / services | Charges | Claim payments | CAS total | PR subset of CAS | PLB net | BPR payment |
|---|---:|---:|---:|---:|---:|---:|---:|
| [Single paid](samples/01-single-paid.835) | 1 / 1 | 100.00 | 100.00 | 0.00 | 0.00 | 0.00 | 100.00 |
| [Multi-claim](samples/02-multi-claim-adjustments.835) | 2 / 3 | 260.00 | 190.00 | 70.00 | 20.00 | 0.00 | 190.00 |
| [Provider adjustments](samples/03-provider-plb-adjustments.835) | 1 / 1 | 200.00 | 150.00 | 50.00 | 0.00 | 20.00 | 130.00 |
| [Denied](samples/04-denied-claim.835) | 1 / 1 | 260.00 | 0.00 | 260.00 | 0.00 | 0.00 | 0.00 |

In these deliberately simple files, each claim satisfies `charges = paid + CAS adjustments`. Patient responsibility is already represented in the PR adjustments: do **not** add CLP05 a second time. The multi-claim file has CO45 amounts of 20 and 30, plus PR1 of 20.

Provider adjustments live outside individual claim loops. The third file has claim payment 150, recovery 25 and interest -5. Its net PLB amount is 20, so `BPR02 = 150 - (25 + -5) = 130`. A positive PLB reduces payment; a negative one increases it. This exercise does not prescribe how to post a real recovery or interest amount. [BCBSMT's provider explanation](https://www.bcbsmt.com/docs/provider/mt/claims/payment/mt-govt-plb-segment-835-era.pdf) describes this sign convention.

## Delimiters, padding and controls

The fixtures use `*` between elements, `:` inside composites, `^` as the repetition delimiter, and `~` after segments. The line breaks after `~` are for people reading the files. Read delimiters from the ISA for arbitrary input; do not assume every payer uses these characters. Keep ISA's fixed-width spaces: its header is 106 ASCII bytes including the segment terminator. Empty positions, such as the blanks in `NM1`, are significant.

Three separate control pairs are checked: ISA13/IEA02, GS06/GE02 and ST02/SE02. SE01 includes both ST and SE; GE01 and IEA01 count the transaction sets and groups, respectively. These examples have exactly one of each. Matching controls alone do not establish conformance.

## Important elements used here

| Element(s) | Meaning in these examples |
|---|---|
| ISA01–04 | No authorisation/security information; blank fixed-width fields. These are not account credentials. |
| ISA05/07,06/08 | ZZ qualifiers and padded invented sender/receiver identifiers. |
| ISA09/10,11,12,13,14,15,16 | Date/time, repetition separator, envelope version, interchange control, acknowledgement request 0, test indicator T and component separator. |
| GS01–08 | HP group, application sender/receiver, date/time, group control, agency X and implementation identifier. |
| ST01/02 | Transaction type 835 and its control number. |
| BPR01–04,16 | Handling code, amount, credit/debit flag, method and date; empty financial fields stay empty. Nonzero files use remittance-only I with CHK; zero-payment file uses notification H with NON. No bank instructions are supplied. |
| TRN01–03 | Trace type 1, invented reference and all-zero originator placeholder. |
| DTM01/02 | Qualifier 405 for production date or 472 for service date, followed by YYYYMMDD. |
| N101/02/03/04 | Role PR/PE, name, optional identifier qualifier FI and fake tax identifier. |
| LX01 | Sequence label introducing the claim grouping used in these examples. |
| CLP01–07 | Claim ID, adjudication status, charge, paid, patient share, filing indicator 12 (PPO) and payer claim control. Status 1 means primary processing, not necessarily payment. |
| NM101/02/03/04/08/09 | Patient role QC, individual 1, invented surname/given name, MI qualifier and fake member ID. |
| SVC01/02/03 | HC-qualified procedure, charge and paid amount. Revenue code and unit fields are omitted in these fixtures. |
| CAS01/02/03 | Group, reason and amount. CO denotes contractual adjustment category; PR denotes patient responsibility. Additional CAS reason/amount/quantity triplets are possible in general but are absent here. |
| PLB01/02/03–06 | Provider ID, fiscal-year-end date, then two adjustment-identifier/amount pairs. A colon separates reason from invented reference. |
| SE01/02; GE01/02; IEA01/02 | Nested counts and their matching controls. |

## Current code context

These examples use CARC 1 for a deductible, CARC 45 for a fee/contract-related reduction and CARC 31 for a patient who cannot be identified as insured, paraphrased from the [X12 CARC list](https://x12.org/codes/claim-adjustment-reason-codes). CO45 is used for a partial reduction, never the complete charge. PLB WO is an overpayment recovery and L6 is interest, from [X12's provider adjustment list](https://x12.org/codes/provider-adjustment-reason-codes).

The fourth file uses CLP02 status 4 for the specific invented scenario of an unrecognised patient/subscriber and no forwarding to another payer. It is **not** a generic zero-payment flag. A recognised patient's claim processed with no payment may retain status 1, 2 or 3. See [X12 RFI 1423](https://x12.org/resources/requests-for-interpretation/rfi-1423-835-clp02-claim-status-code-4). This distinction matters when building denial filters.

A code alone does not decide liability, an appeal or rebilling. Use the full remittance, contract and payer guidance. These are simplified coding illustrations, not billing advice.

## Every segment, in file order

The same envelope pattern is repeated so each file stands alone. The annotations explicitly identify each occurrence rather than requiring a reader to infer which claim owns a service adjustment.

### 01-single-paid.835

[Open the file](samples/01-single-paid.835). Segment numbers below are file order, including envelopes.

| # | Segment | What to read in this occurrence |
|---:|---|---|
| 1 | `ISA*00*          *00*          *ZZ*VISERASYNTHETIC*ZZ*TESTRECEIVER   *261113*0115*^*00501*000000101*0*T*:` | Test envelope: fake padded sender/receiver, controls, date/time and delimiters. ISA15=T. |
| 2 | `GS*HP*VISERASYNTHETIC*TESTRECEIVER*20261113*0115*101*X*005010X221A1` | Health-care payment group HP; fake application IDs; date/time; group control; X12 agency and 005010X221A1 identifier. |
| 3 | `ST*835*0101` | 835 transaction starts; control 0101 must match SE02. |
| 4 | `BPR*I*100.00*C*CHK************20261113` | Payment amount 100.00; credit C; remittance-information-only I / check CHK. This file does not initiate a transfer. |
| 5 | `TRN*1*TEST-TRACE-101*0000000000` | Trace type 1; invented trace and all-zero originator placeholder. No real check, EFT or bank account. |
| 6 | `DTM*405*20261113` | Production date for this invented remittance. |
| 7 | `N1*PR*SYNTHETIC PAYER` | Payer role PR and invented organisation name. |
| 8 | `N1*PE*SYNTHETIC CLINIC*FI*000000000` | Payee role PE, invented clinic, FI qualifier and deliberately fake all-zero tax ID. |
| 9 | `LX*101` | Loop sequence label; it is not a service code or a monetary value. |
| 10 | `CLP*TEST-IGNORE-101*1*100.00*100.00*0.00*12*TEST-PAYER-CLAIM-101` | Invented claim TEST-IGNORE-101; status 1; charge 100.00, paid 100.00, patient responsibility 0.00; filing indicator 12; fake payer control. |
| 11 | `NM1*QC*1*SYNTHETIC*TEST101****MI*TEST-MEMBER-101` | Patient role QC, individual 1, invented name; MI identifies the invented member ID. Empty middle/prefix/suffix fields preserve positions. |
| 12 | `SVC*HC:99213*100.00*100.00` | HC procedure composite HC:99213; service charge 100.00 and service paid 100.00. Revenue code and unit fields are omitted. |
| 13 | `DTM*472*20261101` | Service date for the preceding SVC, not the payment date. |
| 14 | `SE*12*0101` | Transaction trailer: 12 segments including ST and SE; control 0101 matches ST02. |
| 15 | `GE*1*101` | One transaction set in this group; group control matches GS06. |
| 16 | `IEA*1*000000101` | One functional group in this interchange; nine-digit control matches ISA13. |

### 02-multi-claim-adjustments.835

[Open the file](samples/02-multi-claim-adjustments.835). Segment numbers below are file order, including envelopes.

| # | Segment | What to read in this occurrence |
|---:|---|---|
| 1 | `ISA*00*          *00*          *ZZ*VISERASYNTHETIC*ZZ*TESTRECEIVER   *261113*0115*^*00501*000000102*0*T*:` | Test envelope: fake padded sender/receiver, controls, date/time and delimiters. ISA15=T. |
| 2 | `GS*HP*VISERASYNTHETIC*TESTRECEIVER*20261113*0115*102*X*005010X221A1` | Health-care payment group HP; fake application IDs; date/time; group control; X12 agency and 005010X221A1 identifier. |
| 3 | `ST*835*0102` | 835 transaction starts; control 0102 must match SE02. |
| 4 | `BPR*I*190.00*C*CHK************20261113` | Payment amount 190.00; credit C; remittance-information-only I / check CHK. This file does not initiate a transfer. |
| 5 | `TRN*1*TEST-TRACE-102*0000000000` | Trace type 1; invented trace and all-zero originator placeholder. No real check, EFT or bank account. |
| 6 | `DTM*405*20261113` | Production date for this invented remittance. |
| 7 | `N1*PR*SYNTHETIC PAYER` | Payer role PR and invented organisation name. |
| 8 | `N1*PE*SYNTHETIC CLINIC*FI*000000000` | Payee role PE, invented clinic, FI qualifier and deliberately fake all-zero tax ID. |
| 9 | `LX*201` | Loop sequence label; it is not a service code or a monetary value. |
| 10 | `CLP*TEST-IGNORE-201*1*200.00*130.00*20.00*12*TEST-PAYER-CLAIM-201` | Invented claim TEST-IGNORE-201; status 1; charge 200.00, paid 130.00, patient responsibility 20.00; filing indicator 12; fake payer control. |
| 11 | `NM1*QC*1*SYNTHETIC*TEST201****MI*TEST-MEMBER-201` | Patient role QC, individual 1, invented name; MI identifies the invented member ID. Empty middle/prefix/suffix fields preserve positions. |
| 12 | `SVC*HC:99213*120.00*80.00` | HC procedure composite HC:99213; service charge 120.00 and service paid 80.00. Revenue code and unit fields are omitted. |
| 13 | `DTM*472*20261101` | Service date for the preceding SVC, not the payment date. |
| 14 | `CAS*CO*45*20.00` | Service adjustment group CO, reason 45, amount 20.00. Keep this adjustment with its preceding service. |
| 15 | `CAS*PR*1*20.00` | Service adjustment group PR, reason 1, amount 20.00. Patient-share amount already included in the adjustment total. |
| 16 | `SVC*HC:99214*80.00*50.00` | HC procedure composite HC:99214; service charge 80.00 and service paid 50.00. Revenue code and unit fields are omitted. |
| 17 | `DTM*472*20261101` | Service date for the preceding SVC, not the payment date. |
| 18 | `CAS*CO*45*30.00` | Service adjustment group CO, reason 45, amount 30.00. Keep this adjustment with its preceding service. |
| 19 | `LX*202` | Loop sequence label; it is not a service code or a monetary value. |
| 20 | `CLP*TEST-IGNORE-202*1*60.00*60.00*0.00*12*TEST-PAYER-CLAIM-202` | Invented claim TEST-IGNORE-202; status 1; charge 60.00, paid 60.00, patient responsibility 0.00; filing indicator 12; fake payer control. |
| 21 | `NM1*QC*1*SYNTHETIC*TEST202****MI*TEST-MEMBER-202` | Patient role QC, individual 1, invented name; MI identifies the invented member ID. Empty middle/prefix/suffix fields preserve positions. |
| 22 | `SVC*HC:99212*60.00*60.00` | HC procedure composite HC:99212; service charge 60.00 and service paid 60.00. Revenue code and unit fields are omitted. |
| 23 | `DTM*472*20261101` | Service date for the preceding SVC, not the payment date. |
| 24 | `SE*22*0102` | Transaction trailer: 22 segments including ST and SE; control 0102 matches ST02. |
| 25 | `GE*1*102` | One transaction set in this group; group control matches GS06. |
| 26 | `IEA*1*000000102` | One functional group in this interchange; nine-digit control matches ISA13. |

### 03-provider-plb-adjustments.835

[Open the file](samples/03-provider-plb-adjustments.835). Segment numbers below are file order, including envelopes.

| # | Segment | What to read in this occurrence |
|---:|---|---|
| 1 | `ISA*00*          *00*          *ZZ*VISERASYNTHETIC*ZZ*TESTRECEIVER   *261113*0115*^*00501*000000103*0*T*:` | Test envelope: fake padded sender/receiver, controls, date/time and delimiters. ISA15=T. |
| 2 | `GS*HP*VISERASYNTHETIC*TESTRECEIVER*20261113*0115*103*X*005010X221A1` | Health-care payment group HP; fake application IDs; date/time; group control; X12 agency and 005010X221A1 identifier. |
| 3 | `ST*835*0103` | 835 transaction starts; control 0103 must match SE02. |
| 4 | `BPR*I*130.00*C*CHK************20261113` | Payment amount 130.00; credit C; remittance-information-only I / check CHK. This file does not initiate a transfer. |
| 5 | `TRN*1*TEST-TRACE-103*0000000000` | Trace type 1; invented trace and all-zero originator placeholder. No real check, EFT or bank account. |
| 6 | `DTM*405*20261113` | Production date for this invented remittance. |
| 7 | `N1*PR*SYNTHETIC PAYER` | Payer role PR and invented organisation name. |
| 8 | `N1*PE*SYNTHETIC CLINIC*FI*000000000` | Payee role PE, invented clinic, FI qualifier and deliberately fake all-zero tax ID. |
| 9 | `LX*301` | Loop sequence label; it is not a service code or a monetary value. |
| 10 | `CLP*TEST-IGNORE-301*1*200.00*150.00*0.00*12*TEST-PAYER-CLAIM-301` | Invented claim TEST-IGNORE-301; status 1; charge 200.00, paid 150.00, patient responsibility 0.00; filing indicator 12; fake payer control. |
| 11 | `NM1*QC*1*SYNTHETIC*TEST301****MI*TEST-MEMBER-301` | Patient role QC, individual 1, invented name; MI identifies the invented member ID. Empty middle/prefix/suffix fields preserve positions. |
| 12 | `SVC*HC:99214*200.00*150.00` | HC procedure composite HC:99214; service charge 200.00 and service paid 150.00. Revenue code and unit fields are omitted. |
| 13 | `DTM*472*20261101` | Service date for the preceding SVC, not the payment date. |
| 14 | `CAS*CO*45*50.00` | Service adjustment group CO, reason 45, amount 50.00. Keep this adjustment with its preceding service. |
| 15 | `PLB*000000000*20261231*WO:TEST-RECOVERY-301*25.00*L6:TEST-INTEREST-301*-5.00` | Fake provider ID; fiscal-year-end 20261231; WO recovery +25 and L6 interest -5. Net +20 reduces the remittance from 150 to 130. |
| 16 | `SE*14*0103` | Transaction trailer: 14 segments including ST and SE; control 0103 matches ST02. |
| 17 | `GE*1*103` | One transaction set in this group; group control matches GS06. |
| 18 | `IEA*1*000000103` | One functional group in this interchange; nine-digit control matches ISA13. |

### 04-denied-claim.835

[Open the file](samples/04-denied-claim.835). Segment numbers below are file order, including envelopes.

| # | Segment | What to read in this occurrence |
|---:|---|---|
| 1 | `ISA*00*          *00*          *ZZ*VISERASYNTHETIC*ZZ*TESTRECEIVER   *261113*0115*^*00501*000000104*0*T*:` | Test envelope: fake padded sender/receiver, controls, date/time and delimiters. ISA15=T. |
| 2 | `GS*HP*VISERASYNTHETIC*TESTRECEIVER*20261113*0115*104*X*005010X221A1` | Health-care payment group HP; fake application IDs; date/time; group control; X12 agency and 005010X221A1 identifier. |
| 3 | `ST*835*0104` | 835 transaction starts; control 0104 must match SE02. |
| 4 | `BPR*H*0.00*C*NON************20261113` | Payment amount 0.00; credit C; notification H / non-payment NON. |
| 5 | `TRN*1*TEST-TRACE-104*0000000000` | Trace type 1; invented trace and all-zero originator placeholder. No real check, EFT or bank account. |
| 6 | `DTM*405*20261113` | Production date for this invented remittance. |
| 7 | `N1*PR*SYNTHETIC PAYER` | Payer role PR and invented organisation name. |
| 8 | `N1*PE*SYNTHETIC CLINIC*FI*000000000` | Payee role PE, invented clinic, FI qualifier and deliberately fake all-zero tax ID. |
| 9 | `LX*401` | Loop sequence label; it is not a service code or a monetary value. |
| 10 | `CLP*TEST-IGNORE-401*4*260.00*0.00*0.00*12*TEST-PAYER-CLAIM-401` | Invented claim TEST-IGNORE-401; status 4; charge 260.00, paid 0.00, patient responsibility 0.00; filing indicator 12; fake payer control. |
| 11 | `NM1*QC*1*SYNTHETIC*TEST401****MI*TEST-MEMBER-401` | Patient role QC, individual 1, invented name; MI identifies the invented member ID. Empty middle/prefix/suffix fields preserve positions. |
| 12 | `SVC*HC:99215*260.00*0.00` | HC procedure composite HC:99215; service charge 260.00 and service paid 0.00. Revenue code and unit fields are omitted. |
| 13 | `DTM*472*20261101` | Service date for the preceding SVC, not the payment date. |
| 14 | `CAS*CO*31*260.00` | Service adjustment group CO, reason 31, amount 260.00. Keep this adjustment with its preceding service. |
| 15 | `SE*13*0104` | Transaction trailer: 13 segments including ST and SE; control 0104 matches ST02. |
| 16 | `GE*1*104` | One transaction set in this group; group control matches GS06. |
| 17 | `IEA*1*000000104` | One functional group in this interchange; nine-digit control matches ISA13. |

## What the local validator checks

The script reads the four files from the manifest using decimal arithmetic. It checks fixed-width ISA fields/delimiter positions and test markers; the three control pairs; transaction/group/interchange counts; BPR date position; each claim's service sums and adjustment balance; PR as a subset; the signed PLB-to-BPR balance; and the manifest totals. It also proves that a changed trailer count, claim amount or PLB sign is rejected in memory with `--self-test`.

It does not check every licensed implementation rule, trading-partner policy, identifier registry, remark-code requirement, semantic scenario or parser behaviour. It does not contact a network or transmit a file.

## Related reading, with affiliation disclosed

- Reading order: [How to read an 835 ERA file](https://viseraapp.com/guides/how-to-read-an-835-era-file?utm_source=github-samples&utm_medium=referral&utm_campaign=growth-20261113).
- Segment context and PLB: [835 segments explained](https://viseraapp.com/guides/835-segments-explained?utm_source=github-samples&utm_medium=referral&utm_campaign=growth-20261113).
- Code context: [Claim adjustment codes](https://viseraapp.com/guides/claim-adjustment-codes?utm_source=github-samples&utm_medium=referral&utm_campaign=growth-20261113).
- Statement versus transaction: [835 versus EOB](https://viseraapp.com/guides/835-vs-eob?utm_source=github-samples&utm_medium=referral&utm_campaign=growth-20261113).

## References checked November 13, 2026

The original annotations are concise teaching explanations. No licensed X12 implementation guide or complete code list is reproduced in this repository.

- X12's [CARCs](https://x12.org/codes/claim-adjustment-reason-codes) and [provider adjustments](https://x12.org/codes/provider-adjustment-reason-codes) are the primary code references.
- BCBSMT's [PLB explanation](https://www.bcbsmt.com/docs/provider/mt/claims/payment/mt-govt-plb-segment-835-era.pdf) supports the signed payment calculation; its payer-specific posting instructions are not generalised here.
- Stedi's public 5010 reference pages for [ISA](https://www.stedi.com/edi/x12-005010/segment/ISA), [GS](https://www.stedi.com/edi/x12-005010/segment/GS), [BPR](https://www.stedi.com/edi/x12-005010/segment/BPR), [TRN](https://www.stedi.com/edi/x12-005010/segment/TRN), [DTM](https://www.stedi.com/edi/x12-005010/segment/DTM), [N1](https://www.stedi.com/edi/x12-005010/segment/N1), [LX](https://www.stedi.com/edi/x12-005010/segment/LX), [CLP](https://www.stedi.com/edi/x12-005010/segment/CLP), [NM1](https://www.stedi.com/edi/x12-005010/segment/NM1), [SVC](https://www.stedi.com/edi/x12-005010/segment/SVC), [CAS](https://www.stedi.com/edi/x12-005010/segment/CAS), [PLB](https://www.stedi.com/edi/x12-005010/segment/PLB), [SE](https://www.stedi.com/edi/x12-005010/segment/SE), [GE](https://www.stedi.com/edi/x12-005010/segment/GE) and [IEA](https://www.stedi.com/edi/x12-005010/segment/IEA) supplied element context. Generic references do not replace the applicable implementation guide.
- [Handling-code reference](https://www.stedi.com/edi/x12-005010/element/305), [payment-method reference](https://www.stedi.com/edi/x12-005010/element/591).

The original files, annotations and validator are available under the included MIT license. Third-party specifications, code lists and trademarks remain with their owners. No affiliation with X12, Stedi, BCBSMT or a payer is implied.
