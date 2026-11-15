"""Prepare the August 2016 Farmer's Handbook for retrieval."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

import pymupdf as pdf

CHAPTERS = (
    (9, 39, "General Conditions for Cultivation of Crops"),
    (41, 77, "Soil and Plant Nutrition"),
    (79, 104, "Plant Protection"),
    (105, 106, "Categories of Pesticides and Precautions"),
    (107, 127, "Farm Management"),
    (129, 137, "Occupational Health and Safety"),
    (139, 144, "Farmer’s Access to Services"),
)
FIGURE_OCR = {10, 97, 98, 99}
DISEASE_TABLE = range(87, 92)
DISEASE_HEADERS = ("Crops", "Disease", "Symptoms", "Control Measures")
TITLE = "Farmer’s Handbook on Basic Agriculture"


def chapter_for(page_number):
    return next((title for first, last, title in CHAPTERS
                 if first <= page_number <= last), None)


def clean_text(text):
    text = unicodedata.normalize("NFC", text).translate(str.maketrans(
        {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ff", "\u00ad": ""}
    ))
    return re.sub(r"\s+", " ", text).strip()


def rectangles_overlap(first, second):
    return (first & second).get_area() > 0.5 * first.get_area()


def extract_text_blocks(page, excluded_regions):
    """Keep blocks independent so columns do not interleave."""
    for x0, y0, x1, y1, raw, *_ in page.get_text("blocks", sort=True):
        bounds = pdf.Rect(x0, y0, x1, y1)
        if y1 <= 25 or y0 >= 809:
            continue
        if any(rectangles_overlap(bounds, region) for region in excluded_regions):
            continue
        cleaned = clean_text(raw)
        if cleaned:
            yield cleaned, list(bounds)


def extract_tables(page):
    """Save geometry, rows and cells for reviewing the original table layout."""
    for table in page.find_tables().tables:
        yield {
            "bbox": list(table.bbox),
            "rows": table.extract(),
            "row_bboxes": [list(row.bbox) for row in table.rows],
        }


def disease_records(table, metadata):
    rows = table["rows"]
    if not rows or tuple(clean_text(cell or "") for cell in rows[0]) != DISEASE_HEADERS:
        return []
    records = []
    crop = None
    for row_index, row in enumerate(rows[1:], 1):
        if len(row) != 4:
            continue
        crop_cell, disease, symptoms, controls = row
        if crop_cell and clean_text(crop_cell):
            crop = re.sub(r"\s+cont\.*$", "", clean_text(crop_cell), flags=re.I)
        if not (crop and disease and symptoms):
            continue
        # These labels contain known line-break splits in this handbook.
        disease = clean_text(re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", disease))
        disease = re.sub(r"^\d+\.\s*", "", disease)
        fields = {
            "crop": crop.lower(),
            "disease": disease,
            "symptoms": clean_text(symptoms),
            "control_measures_source": clean_text(controls or ""),
        }
        records.append({
            **metadata, **fields, "content_type": "table_row",
            "bbox": table["row_bboxes"][row_index],
            "text": f"Crop: {crop}. Disease: {disease}. Symptoms: {fields['symptoms']}",
            "control_measures_review_required": bool(controls),
        })
    return records


def read_image_text(image_path, tesseract, rotate):
    """OCR image labels; try both sideways orientations for the flowchart."""
    if not tesseract:
        return ""
    candidates = [image_path]
    if rotate:
        from PIL import Image
        with Image.open(image_path) as image:
            for angle in (90, 270):
                rotated = image_path.with_name(f"{image_path.stem}-{angle}.png")
                image.rotate(angle, expand=True).save(rotated)
                candidates.append(rotated)
    outputs = []
    try:
        for candidate in candidates:
            result = subprocess.run(
                [tesseract, str(candidate), "stdout", "-l", "eng", "--psm", "11"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                check=True, timeout=60,
            )
            outputs.append(clean_text(result.stdout))
    finally:
        for candidate in candidates[1:]:
            candidate.unlink(missing_ok=True)
    return max(outputs, key=lambda text: len(re.findall(r"\b[a-zA-Z]{3,}\b", text)))


def extract_figures(page, metadata, output, tesseract):
    page_number = metadata["pdf_page"]
    for index, image in enumerate(page.get_image_info(), 1):
        bounds = pdf.Rect(image["bbox"]) & page.rect
        if bounds.width < 35 or bounds.height < 35:
            continue
        path = output / "figures" / f"p{page_number:03d}-{index:02d}.png"
        page.get_pixmap(clip=bounds, dpi=230 if page_number in FIGURE_OCR else 130,
                        alpha=False).save(path)
        ocr_text = ""
        status = "not_selected"
        if page_number in FIGURE_OCR:
            status = "disabled"
            if tesseract:
                try:
                    ocr_text = read_image_text(path, tesseract, page_number == 10)
                    status = "needs_review" if ocr_text else "no_text_found"
                except (OSError, subprocess.SubprocessError) as error:
                    status = f"failed: {type(error).__name__}"
        yield {
            **metadata, "content_type": "figure", "bbox": list(bounds),
            "image_path": path.relative_to(output).as_posix(),
            "ocr_text": ocr_text, "ocr_status": status,
            "review_required": True,
        }


def process_page(page, document_id, output, tesseract):
    page_number = page.number + 1
    chapter = chapter_for(page_number)
    images = page.get_image_info()
    profile = {
        "pdf_page": page_number,
        "printed_page": page_number - 8 if 9 <= page_number <= 152 else None,
        "chapter": chapter,
        "native_characters": len(page.get_text().strip()),
        "image_instances": len(images),
        "vector_paths": len(page.get_drawings()),
        "included": chapter is not None,
        "table_candidates": 0,
    }
    if not chapter:
        return profile, [], [], []
    metadata = {key: profile[key] for key in ("pdf_page", "printed_page", "chapter")}
    metadata.update(document_id=document_id, document_title=TITLE, edition_year=2016)
    tables = list(extract_tables(page))
    profile["table_candidates"] = len(tables)
    review_tables = [
        {**metadata, **table, "table_index": index, "review_required": True}
        for index, table in enumerate(tables, 1)
    ]
    # Disease grids were checked against the source. Keep remaining detected
    # grids in a review queue, since layout and diagrams can resemble tables.
    structured = [record for table in tables for record in disease_records(table, metadata)
                  if page_number in DISEASE_TABLE]
    excluded = [pdf.Rect(table["bbox"]) for table in tables]
    text_records = [
        {**metadata, "content_type": "text", "crop": None, "bbox": bounds, "text": text}
        for text, bounds in extract_text_blocks(page, excluded)
    ]
    figures = list(extract_figures(page, metadata, output, tesseract))
    return profile, text_records + structured, review_tables, figures


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def preprocess(source, output, tesseract):
    if output.exists() and any(output.iterdir()):
        raise SystemExit("Choose a new or empty output directory.")
    with pdf.open(source) as document:
        if len(document) != 154 or "Handbook on Basic Agriculture" not in document[0].get_text():
            raise SystemExit("This layout profile expects the supplied 154-page handbook.")
        document_id = hashlib.sha256(source.read_bytes()).hexdigest()
        (output / "figures").mkdir(parents=True, exist_ok=True)
        profiles, chunks, tables, figures = [], [], [], []
        for page in document:
            profile, records, detected_tables, extracted_figures = process_page(
                page, document_id, output, tesseract
            )
            profiles.append(profile)
            for ordinal, record in enumerate(records, 1):
                record["id"] = f"{document_id}:{page.number + 1}:{ordinal}"
                chunks.append(record)
            tables.extend(detected_tables)
            figures.extend(extracted_figures)
        for filename, records in (
            ("pages.jsonl", profiles), ("chunks.jsonl", chunks),
            ("tables_review.jsonl", tables), ("figures_review.jsonl", figures),
        ):
            write_jsonl(output / filename, records)
        print(f"Pages: {len(profiles)}; chunks: {len(chunks)}; "
              f"table candidates: {len(tables)}; figure crops: {len(figures)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ocr", action="store_true", help="Run English Tesseract on selected figures.")
    parser.add_argument("--tesseract", default="tesseract", help="Executable name or full path.")
    args = parser.parse_args()
    tesseract = shutil.which(args.tesseract) if args.ocr else None
    if args.ocr and not tesseract:
        parser.error("Tesseract executable not found. Set PATH or pass --tesseract.")
    preprocess(args.pdf, args.output, tesseract)


if __name__ == "__main__":
    main()
