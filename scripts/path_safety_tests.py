import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.config import BLOB_ROOT
from app.storage import ensure_no_traversal, is_within_blob_root, sanitize_path_segment


def _normalize_model(model: str) -> str:
    return model.replace("/", "_").replace("\\", "_")


def _print_case_lines(cases):
    if not cases:
        return
    label_width = max(len(label) for label, _, _ in cases)
    value_reprs = [repr(value) for _, value, _ in cases]
    value_width = max(len(v) for v in value_reprs)
    for (label, _value, ok), value_repr in zip(cases, value_reprs):
        status = "TRUE" if ok else "FALSE"
        print(f"  {label:<{label_width}} -> {value_repr:<{value_width}} : {status}")


def test_allow_models() -> bool:
    models = [
        "SHV78CM3N/28",
        "BVA-48WN1-M20",
        "WM4080HBA/ 03",
        "ABC.123",
        "A_B-C.1 2",
        "BADGER 500-4"
    ]
    results = []
    all_ok = True
    for model in models:
        try:
            ensure_no_traversal(model)
            normalized = _normalize_model(model)
            sanitize_path_segment(normalized, allow_spaces=True)
            ok = True
        except ValueError:
            ok = False
        results.append(("allow_model", model, ok))
        if not ok:
            all_ok = False
    _print_case_lines(results)
    return all_ok


def test_reject_traversal_models() -> bool:
    bad_models = [
        "../etc/passwd",
        "..",
        "/absolute/path",
        "foo/../bar",
        "foo//bar",
        "C:\\Windows",
        "..\\evil",
        "abc\x00def",
    ]
    results = []
    all_ok = True
    for model in bad_models:
        try:
            ensure_no_traversal(model)
            ok = False
        except ValueError:
            ok = True
        results.append(("reject_traversal_model", model, ok))
        if not ok:
            all_ok = False
    _print_case_lines(results)
    return all_ok


def test_brand_rules() -> bool:
    good_brands = ["lg", "aosmith", "whirlpool", "ge", "samsung", "kitchenaid"]
    bad_brands = ["ge appliances", "../ge", "ge/../../", "..", "", "..\\ge"]
    results = []
    all_ok = True
    for brand in good_brands:
        try:
            sanitize_path_segment(brand, allow_spaces=False)
            ok = True
        except ValueError:
            ok = False
        results.append(("good_brand", brand, ok))
        if not ok:
            all_ok = False
    for brand in bad_brands:
        try:
            sanitize_path_segment(brand, allow_spaces=False)
            ok = False
        except ValueError:
            ok = True
        results.append(("bad_brand", brand, ok))
        if not ok:
            all_ok = False
    _print_case_lines(results)
    return all_ok


def test_blob_root_guard() -> bool:
    inside = BLOB_ROOT / "appliance" / "lg" / "model" / "owner" / "abc.pdf"
    outside = BLOB_ROOT.parent / "evil.pdf"
    inside_ok = is_within_blob_root(str(inside))
    outside_ok = not is_within_blob_root(str(outside))
    results = [
        ("blob_root_inside", str(inside), inside_ok),
        ("blob_root_outside", str(outside), outside_ok),
    ]
    _print_case_lines(results)
    return inside_ok and outside_ok


def run_all() -> bool:
    tests = [
        ("allow_models", test_allow_models),
        ("reject_traversal_models", test_reject_traversal_models),
        ("brand_rules", test_brand_rules),
        ("blob_root_guard", test_blob_root_guard),
    ]
    all_ok = True
    for name, fn in tests:
        ok = False
        try:
            ok = bool(fn())
        except Exception:
            ok = False
        print(f"{name}: {'PASS' if ok else 'FAIL'}")
        if not ok:
            all_ok = False
    return all_ok


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
