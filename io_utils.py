from pathlib import Path


def read_local_file(path_str: str) -> str:
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix in {".txt", ".md", ".csv"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        chunks = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            chunks.append(f"\n--- PAGE {i} ---\n{text}")
        return "".join(chunks)

    if suffix == ".docx":
        from docx import Document
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    raise ValueError(
        f"Unsupported file type {suffix}. Supported: txt, md, csv, pdf, docx"
    )


def collect_investor_material() -> str:
    print("\nDo you want to add your own source material? [y/N]")
    answer = input("> ").strip().lower()
    if answer not in {"y", "yes"}:
        return ""

    materials = []

    print("\nYou can add:")
    print("  1) pasted text")
    print("  2) local file path (txt/md/csv/pdf/docx)")
    print("  3) URL / reference note")
    print("Add as many items as you want. Type DONE when finished.\n")

    while True:
        kind = input("Type TEXT / FILE / URL / DONE: ").strip().upper()
        if kind == "DONE":
            break

        if kind == "TEXT":
            print("Paste text. Type END on a new line when finished:")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            materials.append("\n[INVESTOR PASTED TEXT]\n" + "\n".join(lines))

        elif kind == "FILE":
            path = input("Local file path: ").strip()
            try:
                content = read_local_file(path)
                materials.append(f"\n[INVESTOR FILE: {path}]\n{content}")
                print("Added.")
            except Exception as exc:
                print(f"Could not read file: {exc}")

        elif kind == "URL":
            url = input("URL or reference: ").strip()
            materials.append(f"\n[INVESTOR URL/REFERENCE]\n{url}")

        else:
            print("Unknown option.")

    return "\n".join(materials)
