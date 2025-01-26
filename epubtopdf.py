import ebooklib
from ebooklib import epub
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.units import inch
from reportlab.lib.colors import black, gray
from bs4 import BeautifulSoup
import html2text
import os

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("CustomFont", 9)
        self.drawRightString(
            A4[0] - 30,
            30,
            f"Pagina {self._pageNumber} van {page_count}"
        )

class EPUBToPDFConverter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_styles()
        self.toc_entries = []

    def setup_styles(self):

        self.normal_style = ParagraphStyle(
            'Normal',
            fontName='CustomFont',
            fontSize=11,
            leading=14,
            spaceAfter=10,
            alignment=4, 
            firstLineIndent=0,
            leftIndent=0,     
            rightIndent=0      
        )

        self.h1_style = ParagraphStyle(
            'Heading1',
            fontName='CustomFont-Bold',
            fontSize=24,
            leading=28,
            spaceAfter=20,
            spaceBefore=30,
            alignment=1,
        )

        self.h2_style = ParagraphStyle(
            'Heading2',
            fontName='CustomFont-Bold',
            fontSize=20,
            leading=24,
            spaceAfter=15,
            spaceBefore=25,
            alignment=0,
        )

        self.h3_style = ParagraphStyle(
            'Heading3',
            fontName='CustomFont-Bold',
            fontSize=16,
            leading=20,
            spaceAfter=12,
            spaceBefore=20,
            alignment=0,
        )

        # TOC stijlen
        self.toc_h1_style = ParagraphStyle(
            'TOC1',
            fontName='CustomFont-Bold',
            fontSize=14,
            leading=20,
            spaceAfter=10,
        )

        self.toc_h2_style = ParagraphStyle(
            'TOC2',
            fontName='CustomFont',
            fontSize=12,
            leading=16,
            leftIndent=20,
            spaceAfter=8,
        )

        self.toc_h3_style = ParagraphStyle(
            'TOC3',
            fontName='CustomFont',
            fontSize=10,
            leading=14,
            leftIndent=40,
            spaceAfter=6,
        )

    def create_toc_section(self):
        story = []
        story.append(Paragraph("Content", self.h1_style))
        story.append(Spacer(1, 30))

        for level, text in self.toc_entries:
            if level == 1:
                style = self.toc_h1_style
            elif level == 2:
                style = self.toc_h2_style
            else:
                style = self.toc_h3_style
            story.append(Paragraph(text, style))

        story.append(Spacer(1, 30))
        return story

    def convert(self, epub_path, pdf_path):
        book = epub.read_epub(epub_path)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        pdfmetrics.registerFont(TTFont('CustomFont', 'Arial.ttf'))
        pdfmetrics.registerFont(TTFont('CustomFont-Bold', 'Arial.ttf'))

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                for header in soup.find_all(['h1', 'h2', 'h3']):
                    text = header.get_text().strip()
                    if text:
                        level = int(header.name[1])
                        self.toc_entries.append((level, text))
        story = []

        story.extend(self.create_toc_section())

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')

                for header in soup.find_all(['h1', 'h2', 'h3']):
                    text = header.get_text().strip()
                    if text:
                        if header.name == 'h1':
                            story.append(Paragraph(text, self.h1_style))
                        elif header.name == 'h2':
                            story.append(Paragraph(text, self.h2_style))
                        elif header.name == 'h3':
                            story.append(Paragraph(text, self.h3_style))
                        story.append(Spacer(1, 12))

                for para in soup.find_all('p'):
                    text = para.get_text().strip()
                    if text:
                        story.append(Paragraph(text, self.normal_style))
                        story.append(Spacer(1, 12))

        doc.build(
            story,
            canvasmaker=NumberedCanvas,
        )

converter = EPUBToPDFConverter()
epub_file = "input/destination"
pdf_file = "output/destination"

converter.convert(epub_file, pdf_file)
print("Created files:", [pdf_file])