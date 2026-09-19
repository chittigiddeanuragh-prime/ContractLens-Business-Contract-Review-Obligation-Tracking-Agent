import json
import re
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.pdf_parser import PDFParser
from app.services.clause_segmenter import ClauseSegmenter
from app.services.invariants import validate_clause_invariants


def run_eval():
    eval_dir = Path(__file__).resolve().parent
    samples_dir = eval_dir.parent / "samples"
    expected_path = eval_dir / "segmentation_expected.json"

    if not expected_path.exists():
        print(f"Error: {expected_path} does not exist.")
        return

    with open(expected_path, "r", encoding="utf-8") as f:
        expected_data = json.load(f)

    print("=====================================================")
    print("ContractLens Clause Segmentation Evaluation Benchmarks")
    print("=====================================================\n")

    overall_true_positives = 0
    overall_false_positives = 0
    overall_false_negatives = 0

    for sample_filename, exp_info in expected_data.items():
        sample_path = samples_dir / sample_filename
        if not sample_path.exists():
            print(f"Skipping {sample_filename}: file not found.")
            continue

        with open(sample_path, "rb") as f:
            pdf_bytes = f.read()

        parse_res = PDFParser.parse_pdf_bytes(pdf_bytes)
        if parse_res.get("is_scanned"):
            print(f"Sample {sample_filename} was detected as scanned PDF.")
            continue

        canonical_text = parse_res["canonical_text"]
        pages_data = parse_res["pages_data"]

        extracted_clauses = ClauseSegmenter.segment_contract(canonical_text, pages_data)

        # Invariant Verification
        inv = validate_clause_invariants(canonical_text, extracted_clauses)

        # Compute Boundary Precision & Recall
        def clean(s):
            return re.sub(r"[^A-Z0-9]", "", s.strip().upper())

        exp_headings = set(clean(h) for h in exp_info["expected_headings"])
        act_headings = set()
        for c in extracted_clauses:
            act_headings.add(clean(c.get("number", "")))
            if c.get("heading"):
                act_headings.add(clean(f"{c.get('number', '')} {c.get('heading', '')}"))
                act_headings.add(clean(c.get("heading", "")))

        tp = 0
        for exp in exp_headings:
            if any(exp in act for act in act_headings):
                tp += 1

        fp = max(0, len(extracted_clauses) - tp)
        fn = max(0, len(exp_headings) - tp)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        overall_true_positives += tp
        overall_false_positives += fp
        overall_false_negatives += fn

        print(f"Sample: {sample_filename}")
        print(f"  • Extracted Clauses: {len(extracted_clauses)}")
        print(f"  • Invariants Valid:  {'PASS' if inv['valid'] else 'FAIL'}")
        print(f"  • Precision:         {precision:.2%}")
        print(f"  • Recall:            {recall:.2%}")
        print(f"  • F1 Score:          {f1:.2%}")
        print("-----------------------------------------------------")

    total_p = overall_true_positives / (overall_true_positives + overall_false_positives) if (overall_true_positives + overall_false_positives) > 0 else 0
    total_r = overall_true_positives / (overall_true_positives + overall_false_negatives) if (overall_true_positives + overall_false_negatives) > 0 else 0
    total_f1 = (2 * total_p * total_r) / (total_p + total_r) if (total_p + total_r) > 0 else 0

    print(f"\nOVERALL SEGMENTATION PERFORMANCE:")
    print(f"  • Aggregate Precision: {total_p:.2%}")
    print(f"  • Aggregate Recall:    {total_r:.2%}")
    print(f"  • Aggregate F1 Score:  {total_f1:.2%}")
    print("=====================================================")


if __name__ == "__main__":
    run_eval()
