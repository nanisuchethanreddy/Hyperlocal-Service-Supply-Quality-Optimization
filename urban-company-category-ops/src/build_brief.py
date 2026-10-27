"""Create a two-page A4 leadership decision memo (requires reportlab)."""
import json,csv
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,Color,white
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/Management_Brief.pdf'
rows=json.loads((ROOT/'results/summary.json').read_text())['scenario_kpis']
by={x['scenario']:x for x in rows};a=rows[0];b=by['Quality-Safe Playbook'];peak=by['Peak-Shift Experiment'];onb=by['Pooling + Onboarding']
w,h=A4;blue=HexColor('#1767CF');navy=HexColor('#10213B');gray=HexColor('#52637D');light=HexColor('#F3F7FC');green=HexColor('#087D68');amber=HexColor('#AA6612');line=HexColor('#DDE5EF')
reg='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if Path(reg).exists():
    pdfmetrics.registerFont(TTFont('DV',reg));pdfmetrics.registerFont(TTFont('DVB',bold))
else:
    reg='Helvetica'
F='DV' if Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf').exists() else 'Helvetica'
B='DVB' if F=='DV' else 'Helvetica-Bold'
c=canvas.Canvas(str(OUT),pagesize=A4);c.setTitle('Category Operations | Independent Synthetic Manager Brief')

def text(x,y,s,size=9,color=navy,font=None):
    c.setFillColor(color);c.setFont(font or F,size);c.drawString(x,y,s)

def para(x,top,content,width,size=8.1,leading=12,color=gray,bold=False):
    style=ParagraphStyle('d',fontName=B if bold else F,fontSize=size,leading=leading,textColor=color,spaceAfter=0)
    p=Paragraph(content,style);_,ph=p.wrap(width,1000);p.drawOn(c,x,top-ph);return top-ph

def card(x,y,w0,h0):
    c.setFillColor(light);c.roundRect(x,y,w0,h0,9,fill=1,stroke=0)

def heading(y,num,label):
    text(38,y,num,11,blue,B);text(65,y,label,12,navy,B)
    c.setStrokeColor(line);c.line(38,y-9,w-38,y-9)

def foot(page):
    c.setStrokeColor(line);c.line(38,31,w-38,31)
    text(38,18,'INDEPENDENT PORTFOLIO PROJECT  •  ALL OPERATIONAL RESULTS ARE SYNTHETIC',7,gray,B)
    text(w-58,18,f'{page} / 2',7,gray)

# PAGE 1
c.setFillColor(navy);c.rect(0,h-125,w,125,fill=1,stroke=0)
text(38,h-37,'CATEGORY OPERATIONS  /  HYDERABAD',10,HexColor('#BDD9FC'),B)
text(38,h-70,'Service Supply & Quality Optimization',18,white,B)
text(38,h-92,'Urban services category-management case | Sept 2026 synthetic simulation',9,HexColor('#D7E5F7'))
text(38,h-109,'Not affiliated with Urban Company. No private company data used.',8,HexColor('#D7E5F7'))
margin=38;spacing=10;cw=(w-2*margin-3*spacing)/4
stats=[('BASELINE FILL',f"{a['fill_rate_pct']:.1f}%"),('QUALITY-SAFE FILL',f"{b['fill_rate_pct']:.1f}%"),('INCREMENTAL JOBS',f"+{b['completed']-a['completed']}"),('ON-TIME GAIN',f"+{b['on_time_fulfillment_pct']-a['on_time_fulfillment_pct']:.1f} pp")]
y=h-213
for i,(label,value) in enumerate(stats):
    x=margin+i*(cw+spacing);card(x,y,cw,66)
    text(x+10,y+45,label,7,gray,B);text(x+10,y+14,value,18,green if i in [1,2] else blue,B)
heading(h-233,'01','The management problem')
para(38,h-252,'Uneven demand can leave one locality short of qualified service professionals while another has unused capacity. Broadening supply reach can lift fulfillment, but may worsen start-time punctuality, cancellations and complaints. The model asks which combination of supply sharing, professional onboarding and quality coaching offers the best balance.',w-76,8.8,13)
heading(h-330,'02','Controlled scenario results (18-day evaluation set)')
# Table header
x0=38;y0=h-352
c.setFillColor(navy);c.roundRect(x0,y0-17,w-76,22,4,fill=1,stroke=0)
cols=[(42,'POLICY'),(277,'COMPLETED'),(354,'FILL %'),(411,'ON-TIME / ALL'),(501,'COMPLAINT %')]
for x,t in cols:text(x,y0-10,t,7,white,B)
for i,r in enumerate(rows):
    yy=y0-42-i*30
    if i%2==0:c.setFillColor(light);c.rect(38,yy-9,w-76,29,fill=1,stroke=0)
    f=B if r['scenario']=='Quality-Safe Playbook' else F
    co=green if r['scenario']=='Quality-Safe Playbook' else navy
    for x,t in [(42,r['scenario']),(277,f"{r['completed']:,}"),(354,f"{r['fill_rate_pct']:.1f}"),(411,f"{r['on_time_fulfillment_pct']:.1f}"),(501,f"{r['complaint_pct_of_completed']:.1f}")]:text(x,yy,t,8,co,f)
yb=y0-42-len(rows)*30-2
para(38,yb,'<b>Read the denominator:</b> Baseline is 100% on time <i>among completed orders</i> because the assumed local-only travel proxy stays under 45 min; however, 29.9% of all customer requests are unfulfilled. On-time fulfillment out of <i>all requests</i> rises 70.13% to 78.60% with the recommended policy.',w-76,8,12)
heading(yb-70,'03','Operational decision')
para(38,yb-90,f'<b>Recommended test:</b> Adjacent-zone pooling + 12 screened/onboarded candidates + coaching for 57 low-rated synthetic existing professionals. Complete requests increase <b>{a["completed"]:,} to {b["completed"]:,}</b> (+{b["completed"]-a["completed"]:,}), and complaint incidence is <b>{a["complaint_pct_of_completed"]:.2f}% vs {b["complaint_pct_of_completed"]:.2f}%</b>. Program spending is an assumed <b>₹{b["model_program_spend_inr"]:,}</b> (~₹{b["model_program_spend_inr"]/(b["completed"]-a["completed"]):.0f} per added completion); this is not profit or realized ROI.',w-76,8,12)
foot(1);c.showPage()

# PAGE 2
c.setFillColor(navy);c.rect(0,h-96,w,96,fill=1,stroke=0)
text(38,h-34,'IMPLEMENTATION BLUEPRINT',10,HexColor('#BDD9FC'),B)
text(38,h-63,'From demand signal to operating SOP',18,white,B)
heading(h-124,'04','How the model was built')
steps=[
 ('01','Source context','Use public Hyderabad category listings and public professional-enablement materials for relevance; all model quantities declared synthetic.'),
 ('02','Generate operations','Create 2,954 seeded requests, 96 existing professionals, and 45 candidate records in 8 illustrative zones over 28 days.'),
 ('03','Plan without leakage','Use days 1–10 only for demand-to-supply shortage-pressure ranking; reserve days 11–28 for scenario scoring.'),
 ('04','Execute dispatch','Match trade, slot, available capacity and home or adjacent zone; account for acceptance, cancellation, simulated travel and complaints.'),
 ('05','Evaluate and stress-test','Compare five policies; evaluate 5 seeded runs under normal, 15% higher demand and 10% lower partner availability.')]
y=h-153
for n,hd,body in steps:
    c.setFillColor(light);c.roundRect(38,y-48,w-76,53,6,fill=1,stroke=0)
    text(49,y-15,n,12,blue,B);text(88,y-13,hd,9,navy,B)
    para(88,y-20,body,w-145,7.5,10)
    y-=64
heading(y-10,'05','Key guardrails and practical lessons')
y-=37
points=[
 'Do not confuse assignment, completion, conditional punctuality and punctuality across all incoming requests.',
 'Onboarding requires verified professional readiness and safety training; selection cannot be based on demand pressure alone.',
 f'Peak-shift trial delivered {peak["on_time_fulfillment_pct"]:.2f}% on-time fulfillment, below the quality-safe {b["on_time_fulfillment_pct"]:.2f}%; do not implement without pilot.',
 'Travel time is an assumed one-hop proxy, NOT route data or an official 45-minute UC SLA.',
 'Professional earnings, opt-in flexibility, wages, individual rights and customer safety are not measured; field validation is necessary.' ]
for item in points:
    c.setFillColor(blue);c.circle(43,y-4,3,stroke=0,fill=1)
    newy=para(55,y,item,w-96,7.8,11);y=newy-12
heading(y-9,'06','How to discuss this in a Category Manager interview')
para(38,y-28,'"I analyzed why high customer demand does not automatically translate to completed home-service bookings. I built a reproducible simulation of qualified supply, matching and quality outcomes, identified a fill-rate and punctuality trade-off, and recommended a pilot-ready approach with clear operational controls. The improvements are counterfactual model outputs, not company results."',w-76,8.1,12)
text(38,87,'PUBLIC BUSINESS CONTEXT',8,blue,B)
para(38,80,'Urban Company public Hyderabad service catalog; Urban Company Investor Relations: Service Professional Enablement (June 2024); user-provided campus Category Manager JD, p.2. Model inputs and limitations documented in the GitHub README.',w-76,7.4,10)
foot(2);c.save();print('Created',OUT)
