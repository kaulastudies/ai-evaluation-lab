"""Render the proposal content JSON as selectable-text PDFs.

Usage: python build_documents.py CONTENT_JSON OUTPUT_DIRECTORY
The proposal and private handoff text live in the JSON, not in drawing code.
"""
from pathlib import Path
import sys, json, html, os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

src,out=map(Path,sys.argv[1:3]);out.mkdir(parents=True,exist_ok=True)
raw=src.read_text().replace('{{APPLICATION_CONTACT}}', json.dumps(os.environ.get('APPLICATION_CONTACT', 'Contact supplied privately'))[1:-1])
data=json.loads(raw)
for name,file in [('DV','DejaVuSans.ttf'),('DV-Bold','DejaVuSans-Bold.ttf')]:
 pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+file))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold',italic='DV',boldItalic='DV-Bold')
INK=colors.HexColor('#132A37');TEAL=colors.HexColor('#087D82');GRAY=colors.HexColor('#52666F')
styles={
 'title':ParagraphStyle('title',fontName='DV-Bold',fontSize=23,leading=28,spaceAfter=10,textColor=INK),
 'sub':ParagraphStyle('sub',fontName='DV',fontSize=10.5,leading=15,spaceAfter=15,textColor=GRAY),
 'h':ParagraphStyle('h',fontName='DV-Bold',fontSize=12.3,leading=16,spaceBefore=10,spaceAfter=5,keepWithNext=True,textColor=INK),
 'p':ParagraphStyle('p',fontName='DV',fontSize=10.1,leading=14.8,spaceAfter=8,textColor=INK),
 'small':ParagraphStyle('small',fontName='DV',fontSize=8.6,leading=12.2,spaceAfter=7,textColor=GRAY),
 'cell':ParagraphStyle('cell',fontName='DV',fontSize=9.1,leading=12.5,textColor=INK),
 'head':ParagraphStyle('head',fontName='DV-Bold',fontSize=9.1,leading=12.5,textColor=colors.white)
}
def para(s,k='p'):return Paragraph(s,styles[k])
def footer(c,d):
 c.saveState();c.setFillColor(GRAY);c.setFont('DV',8)
 c.drawString(47,29,'AI Evaluation Lab / 30 October 2026')
 c.drawRightString(565,29,str(d.page));c.restoreState()
for doc in data['documents']:
 story=[]
 for i,page in enumerate(doc['pages']):
  if i:story.append(PageBreak())
  story.append(para(page['title'],'title'))
  if page.get('subtitle'):story.append(para(page['subtitle'],'sub'))
  for b in page['blocks']:
   if b['type'] in ('p','h','small'):story.append(para(b['text'],b['type']))
   elif b['type']=='table':
    rows=[[para(html.escape(str(v)),'head' if j==0 else 'cell') for v in row] for j,row in enumerate(b['rows'])]
    t=Table(rows,colWidths=b['widths'],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),INK),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F0F4F4')]),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#D5DEE0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),b.get('padding',7)),('BOTTOMPADDING',(0,0),(-1,-1),b.get('padding',7))]))
    story.extend([t,Spacer(1,9)])
 SimpleDocTemplate(str(out/doc['filename']),pagesize=(612,792),leftMargin=47,rightMargin=47,topMargin=42,bottomMargin=48,title=doc['title'],author='Rama Chandra Malayanur').build(story,onFirstPage=footer,onLaterPages=footer)
 print(doc['filename'])
