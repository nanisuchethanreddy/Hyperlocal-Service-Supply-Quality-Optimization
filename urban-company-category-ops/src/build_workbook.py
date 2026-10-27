"""Build a polished Excel operations workbook from CSV with artifact_tool.
Optional dependency: artifact_tool. The simulation itself needs only Python stdlib.
"""
from pathlib import Path
import csv,json
from artifact_tool import Workbook,SpreadsheetFile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dashboard/Category_Operations_Dashboard.xlsx'
NAVY='#10213B'; BLUE='#0866CF'; CYAN='#CFEAFF'; GRAY='#F1F5F9'; WHITE='#FFFFFF'; CHARCOAL='#334155'; GREEN='#D9F3E7'; AMBER='#FFF2D0'

def get(name):
    with (ROOT/'results'/name).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def num(x):
    try:
        if x=='':return ''
        if str(x).lstrip('-').isdigit():return int(x)
        return float(x)
    except (ValueError,TypeError):return x

def header(sheet,area):
    sheet.get_range(area).format={'fill':NAVY,'font':{'bold':True,'color':WHITE,'size':10},'row_height':31,'vertical_alignment':'center','wrap_text':True}

def export():
    wb=Workbook.create()
    dash=wb.worksheets.add('Executive Dashboard')
    scores=wb.worksheets.add('Scenario KPIs')
    zon=wb.worksheets.add('Zone Drilldown')
    cat=wb.worksheets.add('Category Drilldown')
    plan=wb.worksheets.add('Onboarding Plan')
    fun=wb.worksheets.add('Candidate Funnel')
    meta=wb.worksheets.add('Model & Sources')
    k=get('scenario_kpis.csv');r=get('segment_kpis.csv');p=get('targeted_onboarding_plan.csv')
    selected=[('scenario','Scenario'),('requests','Requests'),('assigned','Assigned'),('completed','Completed'),
         ('fill_rate_pct','Fill Rate (%)'),('on_time_fulfillment_pct','On-Time Fulfillment (%)'),
         ('on_time_pct_of_completed','On-Time / Completed (%)'),('complaint_pct_of_completed','Complaint Rate (%)'),
         ('cancellation_pct_of_assigned','Cancellation / Assigned (%)'),
         ('partner_slot_utilization_pct','Partner Slot Utilization (%)'),('unsupplied_requests','No Supply'),
         ('partner_declined_requests','Partner Declines'),('model_program_spend_inr','Program Spend (INR)'),
         ('new_partners_selected','New Partners Selected'),('coached_partners','Coached Partners'),
         ('flex_shift_changes','Flexible Shift Changes'),('completed_booking_value_proxy_inr','Completed Value Proxy (INR)'),
         ('partners_active_in_model','Model Partner Count')]
    scores.get_range('A1:R6').values=[[b for a,b in selected]]+[[num(row[a]) for a,b in selected] for row in k]
    header(scores,'A1:R1')
    scores.freeze_panes.freeze_rows(1)
    scores.get_range('A1:A6').format.column_width=24
    scores.get_range('B1:R6').format.column_width=16
    scores.get_range('E2:J6').set_number_format('0.00')
    scores.get_range('M2:M6').set_number_format('#,##0')
    scores.get_range('Q2:Q6').set_number_format('#,##0')
    scores.get_range('A5:R5').format.fill=GREEN
    scores.get_range('A6:R6').format.fill=AMBER
    scores.get_range('E2:F6').conditional_formats.add_color_scale({'minColor':'#FEE2E2','midColor':'#FFF1C2','maxColor':'#D1FAE5'})
    def segment(sheet,field):
        vals=[x for x in r if x['dimension']==field]
        fields=[('scenario','Scenario'),('group',field.title()),('requests','Requests'),('assigned','Assigned'),('completed','Completed'),
                ('fill_rate_pct','Fill Rate (%)'),('on_time_fulfillment_pct','On-Time Fulfillment (%)'),
                ('on_time_pct','On-Time/Completed (%)'),('complaint_pct','Complaints (%)'),('cancel_pct','Cancellations (%)')]
        sheet.get_range(f'A1:J{len(vals)+1}').values=[[x[1] for x in fields]]+[[num(z[x[0]]) for x in fields] for z in vals]
        header(sheet,'A1:J1');sheet.freeze_panes.freeze_rows(1)
        sheet.get_range(f'A1:A{len(vals)+1}').format.column_width=25
        sheet.get_range(f'B1:B{len(vals)+1}').format.column_width=20
        sheet.get_range(f'C1:J{len(vals)+1}').format.column_width=18
        sheet.get_range(f'F2:I{len(vals)+1}').set_number_format('0.0')
        sheet.get_range(f'F2:F{len(vals)+1}').conditional_formats.add_color_scale({'minColor':'#FECACA','midColor':'#FEF3C7','maxColor':'#BBF7D0'})
        sheet.get_range(f'A2:J{len(vals)+1}').format.row_height=19
    segment(zon,'zone');segment(cat,'category')
    pf=[('candidate_id','Candidate ID'),('category','Category'),('zone','Zone'),('screening_score','Screen Score'),
        ('verified','ID Verified'),('training_passed','Training Passed'),('activation_day','Activation Day'),
        ('training_pressure_index','Forecast Demand / Supply'),('next_action','Next Step')]
    plan.get_range('A1:I13').values=[[n for _,n in pf]]+[[num(x[key]) for key,_ in pf] for x in p]
    header(plan,'A1:I1');plan.freeze_panes.freeze_rows(1)
    plan.get_range('A1:A13').format.column_width=20;plan.get_range('B1:C13').format.column_width=22
    plan.get_range('D1:H13').format.column_width=19;plan.get_range('I1:I13').format.column_width=38
    plan.get_range('H2:H13').set_number_format('0.00')
    # Candidate funnel detail + editable auditable count formulas.
    with (ROOT/'data/onboarding_candidates.csv').open(newline='',encoding='utf-8') as f:lead=list(csv.DictReader(f))
    fun.get_range('A1:G46').values=[['Candidate ID','Category','Zone','Score','Verified','Trained','Screening Outcome']]+[[x['candidate_id'],x['category'],x['zone'],int(x['screening_score']),int(x['identity_verified']),int(x['training_passed']),x['status']] for x in lead]
    header(fun,'A1:G1');fun.freeze_panes.freeze_rows(1)
    fun.get_range('A1:F46').format.column_width=17;fun.get_range('G1:G46').format.column_width=30
    fun.get_range('I1:J1').values=[['Funnel Stage','Count']];header(fun,'I1:J1')
    fun.get_range('I2:I7').values=[['Applicants'],['Identity verified'],['Training passed'],['Screened ready'],['Selected'],['Activation rate / applicant (%)']]
    fun.get_range('J2').formulas=[['=COUNTA(A2:A46)']]
    fun.get_range('J3').formulas=[['=COUNTIF(E2:E46,1)']]
    fun.get_range('J4').formulas=[['=COUNTIF(F2:F46,1)']]
    fun.get_range('J5').formulas=[['=COUNTIF(G2:G46,"Ready")']]
    fun.get_range('J6').formulas=[["=COUNTA('Onboarding Plan'!A2:A13)"]]
    fun.get_range('J7').formulas=[['=IFERROR(100*J6/J2,0)']]
    fun.get_range('I1:I7').format.column_width=32;fun.get_range('J1:J7').format.column_width=20
    fun.get_range('J7').set_number_format('0.0')

    dash.merge_cells('A1:Q2');dash.get_range('A1').values=[['SERVICE CATEGORY OPERATIONS | HYDERABAD']]
    dash.get_range('A1:Q2').format={'fill':NAVY,'font':{'bold':True,'color':WHITE,'size':19},'row_height':27,'vertical_alignment':'center'}
    dash.merge_cells('A3:Q3');dash.get_range('A3').values=[['Synthetic 28-day simulation  |  10-day planning window / 18-day evaluation  |  Five policy scenarios  |  Seed 42']]
    dash.get_range('A3:Q3').format={'fill':CYAN,'font':{'color':NAVY,'size':11},'row_height':27}
    blocks=[('A5:D5','A6:D8','BASELINE FILL',"='Scenario KPIs'!E2/100"),
            ('E5:H5','E6:H8','RECOMMENDED FILL',"='Scenario KPIs'!E5/100"),
            ('I5:L5','I6:L8','FILL IMPROVEMENT (PP)',"='Scenario KPIs'!E5-'Scenario KPIs'!E2"),
            ('M5:Q5','M6:Q8','ON-TIME FULFILLMENT GAIN (PP)',"='Scenario KPIs'!F5-'Scenario KPIs'!F2")]
    for title_area,val_area,lab,formula in blocks:
        dash.merge_cells(title_area);dash.get_range(title_area.split(':')[0]).values=[[lab]]
        dash.get_range(title_area).format={'fill':NAVY,'font':{'bold':True,'color':WHITE,'size':10},'row_height':25,'horizontal_alignment':'center'}
        dash.merge_cells(val_area);dash.get_range(val_area.split(':')[0]).formulas=[[formula]]
        dash.get_range(val_area).format={'fill':GRAY,'font':{'bold':True,'color':BLUE,'size':28},'horizontal_alignment':'center','vertical_alignment':'center','row_height':20}
    dash.get_range('A6').set_number_format('0.0%');dash.get_range('E6').set_number_format('0.0%')
    dash.get_range('I6').set_number_format('0.0" pp"');dash.get_range('M6').set_number_format('0.0" pp"')
    dash.merge_cells('A10:Q11');dash.get_range('A10').values=[['RECOMMENDATION: Test the quality-safe playbook in a limited pilot. The model increases fulfilled requests and total on-time completions, but cross-zone pooling can reduce punctuality among completed jobs. Validate travel, earnings and complaints before a live rollout.']]
    dash.get_range('A10:Q11').format={'fill':GREEN,'font':{'color':NAVY,'size':10},'row_height':25,'wrap_text':True,'vertical_alignment':'center'}
    dash.get_range('A29:H29').merge();dash.get_range('A29').values=[['POLICY SCORECARD — metrics are synthetic, not company results']]
    dash.get_range('A29:H29').format={'fill':NAVY,'font':{'bold':True,'color':WHITE},'row_height':26}
    dash.get_range('A30:H30').values=[['Scenario','Requests','Completed','Fill (%)','On-time / all (%)','Complaints (%)','Program spend','Selected']]
    header(dash,'A30:H30')
    for i in range(5):
        j=i+31;s=i+2
        fs=[[f"='Scenario KPIs'!{c}{s}" for c in ['A','B','D','E','F','H','M','N']]]
        dash.get_range(f'A{j}:H{j}').formulas=fs
    dash.get_range('A31:A35').format.column_width=24
    dash.get_range('B31:H35').format.column_width=16
    dash.get_range('D31:F35').set_number_format('0.0')
    dash.get_range('G31:G35').set_number_format('#,##0')
    dash.get_range('A34:H34').format.fill=GREEN
    dash.get_range('A35:H35').format.fill=AMBER
    dash.get_range('A37:Q38').merge();dash.get_range('A37').values=[['Method note: Fill = completed / requested; On-time fulfillment = on-time completed / requested; Complaint rate = complained completed / completed. Travel is a modeled one-hop proxy, not map ETA. No real UC data, prices, earnings, or proprietary metrics are used.']]
    dash.get_range('A37:Q38').format={'fill':GRAY,'font':{'color':CHARCOAL,'size':10},'wrap_text':True,'vertical_alignment':'center','row_height':25}
    dash.get_range('A1:Q38').format.column_width=13.5
    dash.get_range('A1:A38').format.column_width=24
    # Add two side-by-side chart plots using direct category labels.
    from artifact_tool import ChartPropsInput
    for col,metric,anchor,end,title in [('E','Fill Rate','A13','I27','Completed request rate (%)'),('F','On-Time','J13','Q27','On-time completed / requested (%)')]:
        cp:ChartPropsInput={'title':title,'has_legend':False}
        ch=dash.charts.add('bar',cp)
        ch.bar_options.direction='column';ch.bar_options.grouping='clustered'
        series=ch.series.add(metric)
        series.category_formula="'Scenario KPIs'!$A$2:$A$6"
        series.formula=f"'Scenario KPIs'!${col}$2:${col}$6"
        ch.set_position(anchor,end)
    # References and model rules; URLs are NOT sources for synthetic order volumes.
    notes=[
      ('CLASSIFICATION','RESEARCH BASIS','REFERENCE / ASSUMPTION'),
      ('Official service catalog','Three modeled categories reflect available Hyderabad listings','https://www.urbancompany.com/Hyderabad'),
      ('Official partner program','Training, certification, quality & fulfillment are real operating concerns','https://investorrelations.urbancompany.com/announcements-and-highlights/service-professional-enablement'),
      ('Provided campus JD','Local supply, daily city operations, quality initiatives','User-provided Campus Category Manager (Business Operations).pdf, page 2'),
      ('Synthetic study period','Sept 1–28, 2026','Planning days 1–10; holdout days 11–28'),
      ('Existing partner cohort',96,'Generated, not UC partner count'),
      ('Candidate funnel',45,'Synthetic screened applicants'),
      ('New partners selected',12,'Based on first 10 days gap proxy; activate from day 13'),
      ('Travel service level','<= 45 min estimated travel proxy','Assumed; not a public UC SLA'),
      ('Service price proxy','INR 550/900/1100 depending on category','Illustrative; not actual UC item prices / commissions'),
      ('Onboarding unit cost','INR 1,500','Illustrative program budget assumption'),
      ('Coaching unit cost','INR 450','Illustrative program budget assumption'),
      ('Flexible shift experiment','2 slots/partner preserved','Experiment not recommended without local validation'),
      ('Limitations','No real demand, compensation, geography, ratings, or causal field trial','All performance metrics are model outputs')]
    meta.get_range(f'A1:C{len(notes)}').values=[[str(v) for v in row] for row in notes]
    header(meta,'A1:C1');meta.get_range('A1:A20').format.column_width=28
    meta.get_range('B1:B20').format.column_width=47;meta.get_range('C1:C20').format.column_width=82
    meta.get_range('A2:C20').format.row_height=33;meta.get_range('A2:C20').format.wrap_text=True
    # compact verification and export
    print('Workbook KPI check:',wb.inspect({'kind':'table','range':'Executive Dashboard!A30:H35','include':'values,formulas','table_max_rows':6,'table_max_cols':8}).ndjson[:1500])
    OUT.parent.mkdir(parents=True,exist_ok=True)
    SpreadsheetFile.export_xlsx(wb).save(str(OUT))
    try:
        wb.render({'sheet_name':'Executive Dashboard','range':'A1:Q11','scale':1.25}).save(str(ROOT/'dashboard/dashboard_preview.png'))
    except Exception as e:
        print('Nonfatal preview render issue:',repr(e))
    print('Saved',OUT)
if __name__=='__main__':export()
