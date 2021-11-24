from fpdf import FPDF


class PDF(FPDF):
    def header(self):
        # Logo
        self.image("https://www.utpl.edu.ec/manual_imagen/images/vertical/UTPL-INSTITUCIONAL-AZUL.png", 180, 3, 15)
        # Arial bold 15
        self.set_font('Arial', 'B', 13)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, 'UNIVERSIDAD TECNICA PARTICULAR DE LOJA', border=False, ln=1, align='C')
        # Line break
        self.ln(20)

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Curriculum Vitae SIAC')
        self.cell(0, 10, 'Página ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')


class PDFCOMPLETO(FPDF):
    def header(self):
        # Logo
        self.image("https://www.utpl.edu.ec/manual_imagen/images/vertical/UTPL-INSTITUCIONAL-AZUL.png", 180, 3, 15)
        # Arial bold 15
        self.set_font('Arial', 'B', 13)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, 'UNIVERSIDAD TECNICA PARTICULAR DE LOJA', border=False, ln=1, align='C')
        # Line break
        self.ln(20)

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Curriculum Vitae SIAC')
        self.cell(0, 10, 'Página ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')


class PDFRESUMIDO(FPDF):
    def header(self):
        # Logo
        self.image("https://www.utpl.edu.ec/manual_imagen/images/vertical/UTPL-INSTITUCIONAL-AZUL.png", 180, 3, 15)
        # Arial bold 15
        self.set_font('helvetica', 'B', 13)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, 'UNIVERSIDAD TECNICA PARTICULAR DE LOJA', border=False, ln=1, align='C')
        # Line break
        self.ln(20)

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Curriculum Vitae SIAC')
        self.cell(0, 10, 'Página ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')