"""Check this repository's synthetic fixtures, not general X12 conformance.

Run: python validate_examples.py --self-test
Standard library only. No network or file writes.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ZERO = Decimal("0")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(raw: str, fixture: dict) -> dict:
    require(raw.isascii(), "Non-ASCII fixture")
    require(raw.endswith("~\n"), "Missing final segment terminator/newline")
    first = raw.split("\n", 1)[0]
    require(len(first) == 106, "ISA must be 106 bytes including terminator")
    require(first[3] == "*" and first[82] == "^" and first[104:106] == ":~",
            "Unexpected ISA delimiters/positions")
    segments = [segment.strip().split("*") for segment in raw.split("~") if segment.strip()]
    require(all("\n" not in value for p in segments for value in p), "Missing segment terminator")
    tags = [p[0] for p in segments]
    for tag in ("ISA", "GS", "ST", "BPR", "TRN", "SE", "GE", "IEA"):
        require(tags.count(tag) == 1, f"Expected exactly one {tag}")
    require(tags[:4] == ["ISA", "GS", "ST", "BPR"], "Unexpected opening order")
    require(tags[-3:] == ["SE", "GE", "IEA"], "Unexpected closing order")
    isa, gs, st = segments[:3]
    se, ge, iea = segments[-3:]
    require(len(isa) == 17, "ISA element count")
    for i, size in {1:2, 2:10, 3:2, 4:10, 5:2, 6:15, 7:2, 8:15, 9:6, 10:4, 11:1, 12:5, 13:9, 14:1, 15:1, 16:1}.items():
        require(len(isa[i]) == size, f"ISA{i:02} fixed width")
    require(isa[15] == "T", "Missing test interchange marker")
    require(isa[6].strip() == "VISERASYNTHETIC" and isa[8].strip() == "TESTRECEIVER",
            "Missing invented interchange IDs")
    require(isa[13] == iea[2] == fixture["interchange_control"], "ISA/IEA controls differ")
    require(gs[6] == ge[2], "GS/GE controls differ")
    require(st[2] == se[2], "ST/SE controls differ")
    require(st[1] == "835" and gs[1] == "HP" and gs[8] == "005010X221A1",
            "Unexpected transaction/group identifiers")
    st_index, se_index = tags.index("ST"), tags.index("SE")
    require(int(se[1]) == se_index - st_index + 1 == fixture["transaction_segment_count"],
            "SE count differs from included ST..SE segments")
    require(ge[1] == "1" and iea[1] == "1", "Group/interchange count")
    bpr = segments[tags.index("BPR")]
    require(len(bpr) == 17 and bpr[16] == "20261113", "BPR16 payment-date position")
    require(all(value == "" for value in bpr[5:16]), "Unexpected financial identifiers")
    require(bpr[3] == "C", "Credit flag changed")
    require((bpr[1], bpr[4]) == (("H", "NON") if Decimal(bpr[2]) == ZERO else ("I", "CHK")),
            "Handling/payment-method pair")
    datetime.strptime(bpr[16], "%Y%m%d")

    claims, active, service = [], None, None
    provider_adjustments = []
    for p in segments:
        tag = p[0]
        if tag == "CLP":
            require(p[1].startswith("TEST-IGNORE-") and p[7].startswith("TEST-PAYER-CLAIM-"),
                    "Missing synthetic claim IDs")
            active = dict(charge=Decimal(p[3]), paid=Decimal(p[4]), pr=Decimal(p[5]),
                          cas=ZERO, pr_cas=ZERO, services=[])
            claims.append(active)
            service = None
        elif tag == "NM1":
            require(p[3] == "SYNTHETIC" and p[9].startswith("TEST-MEMBER-"),
                    "Unexpected patient/member marker")
        elif tag == "SVC":
            require(active is not None, "Service outside claim")
            service = dict(charge=Decimal(p[2]), paid=Decimal(p[3]), cas=ZERO)
            active["services"].append(service)
        elif tag == "CAS":
            require(active is not None and service is not None, "Expected service-scoped CAS")
            for reason_index in range(2, len(p), 3):
                require(reason_index + 1 < len(p), "CAS reason missing amount")
                amount = Decimal(p[reason_index + 1])
                service["cas"] += amount
                active["cas"] += amount
                if p[1] == "PR":
                    active["pr_cas"] += amount
        elif tag == "PLB":
            require(p[1] == "000000000" and p[2] == "20261231", "PLB fake ID/fiscal-year date")
            require(len(p) % 2 == 1, "PLB reason/amount pairs")
            for reason_index in range(3, len(p), 2):
                require(":TEST-" in p[reason_index], "PLB synthetic reference")
                provider_adjustments.append(Decimal(p[reason_index + 1]))
        elif tag == "N1" and p[1] == "PE":
            require(p[2:] == ["SYNTHETIC CLINIC", "FI", "000000000"], "Fake payee changed")

    for c in claims:
        require(sum((s["charge"] for s in c["services"]), ZERO) == c["charge"],
                "Claim/service charges differ")
        require(sum((s["paid"] for s in c["services"]), ZERO) == c["paid"],
                "Claim/service payments differ")
        require(c["charge"] == c["paid"] + c["cas"], "Claim payment/adjustment balance")
        require(c["pr"] == c["pr_cas"], "PR is already a CAS subset")
        for s in c["services"]:
            require(s["charge"] == s["paid"] + s["cas"], "Service payment/adjustment balance")
    totals = dict(
        claims=len(claims),
        service_lines=sum(len(c["services"]) for c in claims),
        charges=sum((c["charge"] for c in claims), ZERO),
        claim_payments=sum((c["paid"] for c in claims), ZERO),
        cas_adjustments=sum((c["cas"] for c in claims), ZERO),
        patient_responsibility=sum((c["pr"] for c in claims), ZERO),
        provider_adjustments_net=sum(provider_adjustments, ZERO),
        payment=Decimal(bpr[2]),
    )
    require(totals["payment"] == totals["claim_payments"] - totals["provider_adjustments_net"],
            "Signed PLB-to-BPR balance")
    for key, expected in fixture["expected"].items():
        require(totals[key] == (expected if isinstance(expected, int) else Decimal(expected)),
                f"Manifest expectation differs: {key}")
    return {key: (str(value.quantize(Decimal("0.01"))) if isinstance(value, Decimal) else value)
            for key, value in totals.items()}


def self_test(fixtures: list[dict], contents: dict[str, str]) -> None:
    cases = []
    first, multi, plb = fixtures[:3]
    raw = contents[first["file"]]
    old = next(s for s in raw.split("~") if s.strip().startswith("SE*"))
    cases.append(("bad trailer count", raw.replace(old, "\nSE*0*" + old.strip().split("*")[2]), first))
    raw = contents[multi["file"]]
    cases.append(("changed claim payment", raw.replace("*200.00*130.00*", "*200.00*131.00*", 1), multi))
    raw = contents[plb["file"]]
    cases.append(("changed PLB sign", raw.replace("WO:TEST-RECOVERY-301*25.00", "WO:TEST-RECOVERY-301*-25.00", 1), plb))
    for name, broken, fixture in cases:
        require(broken != contents[fixture["file"]], f"Mutation was not applied: {name}")
        try:
            validate(broken, fixture)
        except ValueError:
            print(f"PASS rejection: {name}")
        else:
            raise ValueError(f"Invalid fixture accepted: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    options = parser.parse_args()
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    contents = {}
    for fixture in manifest["fixtures"]:
        path = ROOT / fixture["file"]
        require(path.resolve().is_relative_to(ROOT), "Manifest path escapes repository")
        raw = path.read_text(encoding="ascii")
        contents[fixture["file"]] = raw
        print(f"PASS {fixture['file']}: " + json.dumps(validate(raw, fixture), sort_keys=True))
    if options.self_test:
        self_test(manifest["fixtures"], contents)
    print("Checked four synthetic fixtures; this is not X12 conformance certification.")


if __name__ == "__main__":
    main()
