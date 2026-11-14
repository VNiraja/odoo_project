import ast
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADDON_ROOT = PROJECT_ROOT / "addons" / "custom" / "giftguard_compliance"


def main():
    errors = []
    model_names = set()

    for path in ADDON_ROOT.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            errors.append(f"{path}: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "_name"
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)
                    ):
                        model_names.add(node.value.value)

    try:
        manifest = ast.literal_eval(
            (ADDON_ROOT / "__manifest__.py").read_text(encoding="utf-8")
        )
    except (OSError, SyntaxError, ValueError) as exc:
        errors.append(f"Invalid add-on manifest: {exc}")
        manifest = {}

    for relative_path in manifest.get("data", []):
        if not (ADDON_ROOT / relative_path).is_file():
            errors.append(f"Missing manifest data file: {relative_path}")

    for path in ADDON_ROOT.rglob("*.xml"):
        try:
            ET.parse(path)
        except (OSError, ET.ParseError) as exc:
            errors.append(f"{path}: {exc}")

    access_path = ADDON_ROOT / "security" / "ir.model.access.csv"
    try:
        with access_path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            expected_header = [
                "id",
                "name",
                "model_id:id",
                "group_id:id",
                "perm_read",
                "perm_write",
                "perm_create",
                "perm_unlink",
            ]
            if reader.fieldnames != expected_header:
                errors.append("Unexpected ACL CSV header.")
            rows = list(reader)
        model_refs = {
            "model_" + model_name.replace(".", "_")
            for model_name in model_names
        }
        for row in rows:
            model_ref = row["model_id:id"]
            if model_ref not in model_refs:
                errors.append(f"ACL references an unknown model: {model_ref}")
    except (OSError, KeyError) as exc:
        errors.append(f"Invalid ACL CSV: {exc}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    python_count = len(list(ADDON_ROOT.rglob("*.py")))
    xml_count = len(list(ADDON_ROOT.rglob("*.xml")))
    print(
        f"Validated {python_count} Python files, {xml_count} XML files, "
        "manifest data paths, and ACL model references."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
