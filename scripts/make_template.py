import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors

CHARACTERS =(
     list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    +list("abcdefghijklmnopqrstuvwxyz")
    +list("0123456789")
    +[".", ",", "!", "?", "'", '"', "-", ":", ";", "(", ")"]
)