"""
Génère un PDF à partir des sections du rapport (liste de {"titre","contenu"}).
Parsing minimal du markdown produit par l'IA :
    "### xxx"  -> sous-titre en gras
    "- xxx"    -> puce indentée
    autre      -> paragraphe normal
"""

from fpdf import FPDF


class RapportPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("helvetica", "I", 8)
        self.set_text_color(140, 130, 110)
        self.cell(0, 8, "Rapport Marketing POS", align="L")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(140, 130, 110)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _safe(texte: str) -> str:
    """Les polices de base FPDF (helvetica) ne supportent que le Latin-1.
    On remplace les caractères non encodables plutôt que de planter."""
    return texte.encode("latin-1", "replace").decode("latin-1")


def generer_pdf(sections: list[dict], nombre_commandes: int | None = None) -> bytes:
    pdf = RapportPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- Page de titre façon "ticket de caisse" ---
    pdf.set_font("courier", "B", 20)
    pdf.set_text_color(40, 36, 32)
    pdf.cell(0, 14, _safe("RAPPORT MARKETING"), align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("courier", "", 11)
    pdf.set_text_color(90, 82, 70)
    pdf.cell(0, 8, _safe("=" * 42), align="C", new_x="LMARGIN", new_y="NEXT")
    if nombre_commandes is not None:
        pdf.cell(0, 8, _safe(f"{nombre_commandes} commandes analysées"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, _safe("=" * 42), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    for section in sections:
        pdf.set_font("courier", "B", 13)
        pdf.set_text_color(30, 27, 24)
        pdf.cell(0, 10, _safe(f"» {section['titre'].upper()}"), new_x="LMARGIN", new_y="NEXT")

        pdf.set_draw_color(200, 190, 170)
        pdf.set_line_width(0.3)
        pdf.dashed_line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y(), dash_length=1.5, space_length=1.5)
        pdf.ln(4)

        contenu = section.get("contenu") or "(aucun contenu généré)"
        for ligne in contenu.split("\n"):
            ligne_nettoyee = ligne.strip()
            if not ligne_nettoyee:
                pdf.ln(2)
                continue

            if ligne_nettoyee.startswith("### "):
                pdf.set_font("helvetica", "B", 12)
                pdf.set_text_color(40, 36, 32)
                pdf.multi_cell(0, 7, _safe(ligne_nettoyee[4:]))
            elif ligne_nettoyee.startswith("#"):
                pdf.set_font("helvetica", "B", 12)
                pdf.set_text_color(40, 36, 32)
                pdf.multi_cell(0, 7, _safe(ligne_nettoyee.lstrip("#").strip()))
            elif ligne_nettoyee.startswith("- ") or ligne_nettoyee.startswith("* "):
                pdf.set_font("helvetica", "", 10.5)
                pdf.set_text_color(60, 55, 48)
                pdf.set_x(pdf.l_margin + 5)
                pdf.multi_cell(0, 6, _safe(f"•  {ligne_nettoyee[2:]}"))
            else:
                pdf.set_font("helvetica", "", 10.5)
                pdf.set_text_color(60, 55, 48)
                pdf.multi_cell(0, 6, _safe(ligne_nettoyee))

        pdf.ln(6)

    return bytes(pdf.output())
