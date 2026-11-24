import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Character set: Uppercase, Lowercase, Digits, Common Punctuation
CHARACTERS = (
    list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    + list("abcdefghijklmnopqrstuvwxyz")
    + list("0123456789")
    + [".", ",", "!", "?", "'", '"', "-", ":", ";", "(", ")"]
)

VARIANTS_PER_CHAR = 3 # set it always x<=3
COLS_PER_PAGE = 4  # 4 character groups per row (12 boxes across)
ROWS_PER_PAGE = 8  # 8 rows per page -> 32 characters per page


def draw_fiducial_markers(c: canvas.Canvas, width: float, height: float, margin: float, size: float) -> dict:
    """Draws 4 solid black corner squares used by OpenCV for perspective correction."""
    c.setFillColor(colors.black)
    markers = {
        "top_left": (margin, height - margin - size),
        "top_right": (width - margin - size, height - margin - size),
        "bottom_left": (margin, margin),
        "bottom_right": (width - margin - size, margin),
    }
    for x, y in markers.values():
        c.rect(x, y, size, size, stroke=0, fill=1)

    # Return center coordinates of the 4 markers (origin at top-left for OpenCV compatibility)
    return {
        name: {
            "x_mm": round((x + size / 2) / mm, 2),
            "y_mm": round((height - (y + size / 2)) / mm, 2),
        }
        for name, (x, y) in markers.items()
    }


def generate_template(output_pdf: str = "assets/template_sheet.pdf", output_map: str = "assets/template_map.json"):
    Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)
    Path(output_map).parent.mkdir(parents=True, exist_ok=True)

    width, height = A4  # 210mm x 297mm
    c = canvas.Canvas(output_pdf, pagesize=A4)

    marker_margin = 10 * mm
    marker_size = 8 * mm

    # Inner working area between markers
    work_left = 22 * mm
    work_right = width - 22 * mm
    work_top = height - 32 * mm
    work_bottom = 20 * mm

    work_w = work_right - work_left
    work_h = work_top - work_bottom

    group_w = work_w / COLS_PER_PAGE
    row_h = work_h / ROWS_PER_PAGE

    box_size = 11.5 * mm
    box_gap = 1.2 * mm
    chars_per_page = COLS_PER_PAGE * ROWS_PER_PAGE

    layout_data = {
        "page_size_mm": {"width": round(width / mm, 2), "height": round(height / mm, 2)},
        "variants_per_char": VARIANTS_PER_CHAR,
        "pages": [],
    }

    total_pages = (len(CHARACTERS) + chars_per_page - 1) // chars_per_page

    for page_idx in range(total_pages):
        # Header instructions
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(work_left, height - 16 * mm, f"Handwriting Capture Sheet — Page {page_idx + 1} of {total_pages}")
        c.setFont("Helvetica", 8.5)
        c.setFillColor(colors.HexColor("#444444"))
        c.drawString(
            work_left,
            height - 21 * mm,
            "Write naturally inside each box using dark ink. Keep letters resting on the dashed baseline.",
        )

        markers_meta = draw_fiducial_markers(c, width, height, marker_margin, marker_size)
        page_cells = []

        start_i = page_idx * chars_per_page
        page_chars = CHARACTERS[start_i : start_i + chars_per_page]

        for idx, char in enumerate(page_chars):
            row = idx // COLS_PER_PAGE
            col = idx % COLS_PER_PAGE

            gx = work_left + col * group_w
            gy_top = work_top - row * row_h

            # Character prompt label above the 3 boxes
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 10)
            display_label = f'"{char}"' if char in ["'", '"', ".", ",", ":", ";", "-"] else char
            c.drawString(gx + 1 * mm, gy_top - 4.5 * mm, display_label)

            box_top = gy_top - 6.5 * mm
            box_bottom = box_top - box_size
            baseline_y = box_bottom + (box_size * 0.28)  # 28% from bottom for descenders (g, j, p, y)

            for v in range(VARIANTS_PER_CHAR):
                bx = gx + v * (box_size + box_gap)

                # Outer capture box
                c.setStrokeColor(colors.HexColor("#222222"))
                c.setLineWidth(0.8)
                c.setDash([])
                c.rect(bx, box_bottom, box_size, box_size, stroke=1, fill=0)

                # Dashed baseline guide (light cyan/gray so thresholding drops it cleanly)
                c.setStrokeColor(colors.HexColor("#B8D4E3"))
                c.setLineWidth(0.5)
                c.setDash(2, 2)
                c.line(bx + 0.8 * mm, baseline_y, bx + box_size - 0.8 * mm, baseline_y)

                # Save coordinates in top-left origin (mm) for OpenCV slicing
                page_cells.append({
                    "char": char,
                    "variant": v,
                    "x_mm": round(bx / mm, 2),
                    "y_mm": round((height - box_top) / mm, 2),
                    "w_mm": round(box_size / mm, 2),
                    "h_mm": round(box_size / mm, 2),
                    "baseline_ratio": 0.72,  # Distance from top of box to baseline
                })

        c.setDash([])
        layout_data["pages"].append({
            "page": page_idx + 1,
            "markers": markers_meta,
            "cells": page_cells,
        })
        c.showPage()

    c.save()
    with open(output_map, "w", encoding="utf-8") as f:
        json.dump(layout_data, f, indent=2)

    print(f"Generated {total_pages}-page template -> {output_pdf}")
    print(f"Saved exact cell coordinates -> {output_map}")


if __name__ == "__main__":
    generate_template()