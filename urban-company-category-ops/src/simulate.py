"""Synthetic home-services marketplace simulation, not Urban Company operational data.
Reproducible with standard library only; no external API, private data or commercial pricing.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, random
from collections import defaultdict, Counter
from pathlib import Path
from datetime import date, timedelta

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; OUT=ROOT/'results'
ZONES=[
 ('Gachibowli',1.30,'west'),('Kondapur',1.20,'west'),('Madhapur',1.25,'central'),
 ('HITEC City',1.15,'central'),('Kukatpally',1.05,'north'),('Miyapur',0.85,'north'),
 ('Manikonda',1.05,'west'),('Banjara Hills',1.00,'central')]
# Assumed operating-cell adjacency, NOT actual driving distance or travel APIs.
EDGES={
 'Gachibowli':['Kondapur','Manikonda','HITEC City'],
 'Kondapur':['Gachibowli','Madhapur','HITEC City','Miyapur'],
 'Madhapur':['Kondapur','HITEC City','Banjara Hills'],
 'HITEC City':['Gachibowli','Kondapur','Madhapur','Manikonda'],
 'Kukatpally':['Miyapur','Madhapur'], 'Miyapur':['Kukatpally','Kondapur'],
 'Manikonda':['Gachibowli','HITEC City','Banjara Hills'],
 'Banjara Hills':['Madhapur','Manikonda']}
# Add reverse links to ensure symmetric one-hop proxy.
for a,neighbors in list(EDGES.items()):
    for b in neighbors:
        if a not in EDGES[b]: EDGES[b].append(a)
CATS=[('AC Repair',1.12,900),('Bathroom Cleaning',1.00,1100),('Electrician',1.05,550)]
SLOTS=['Morning','Afternoon','Evening']
DAYS=28; HOLDOUT=10; ONBOARD_DAY=13
SCENARIOS=['Baseline','Zone Pooling','Pooling + Onboarding','Quality-Safe Playbook','Peak-Shift Experiment']
# All amounts represent illustrative model assumptions, NOT UC fees or costs.
ASSUMPTIONS={
 'city':'Hyderabad','simulation_dates':'2026-09-01 to 2026-09-28',
 'training_days':10,'onboarding_start_day':ONBOARD_DAY,'service_slot_hours':4,
 'existing_partners':96,'new_partners_selected':12,
 'max_jobs_per_partner_per_day':2,
 'onboarding_cost_inr_per_partner':1500,
 'partner_coaching_cost_inr_each':450,
 'peak_shift_coordination_cost_inr_each':200,
 'booking_values_are_illustrative':True,
 'on_time_eta_proxy_limit_minutes':45,
 'quality_coaching_cancellation_reduction_relative':0.22,
 'quality_coaching_complaint_reduction_relative':0.25,
 'primary_evaluation_window':'days 11-28 (out-of-sample from 10-day planning window)',
 'geographic_proxy':'illustrative one-hop zone adjacency, not actual road network',
 'partner_quality_score_rule':'synthetic rating less than 4.5 eligible for coaching' 
}

def u01(*parts):
    raw='|'.join(map(str,parts)).encode()
    return int.from_bytes(hashlib.blake2b(raw,digest_size=8).digest(),'big')/(2**64)

def writecsv(path,rows,cols=None):
    rows=list(rows)
    if not rows and not cols:return
    cols=cols or list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(rows)

def get_inputs(seed=42):
    rng=random.Random(seed)
    zn=[z for z,_,_ in ZONES]
    categories=[x[0] for x in CATS]
    zdata=[dict(zone=z,demand_index=m,cluster=cluster,adjacent_zones=';'.join(EDGES[z])) for z,m,cluster in ZONES]
    catdata=[dict(category=name,demand_multiplier=val,model_booking_value_inr=price,
                  note='Illustrative assumptions - not Urban Company prices') for name,val,price in CATS]
    partners=[]
    for i in range(ASSUMPTIONS['existing_partners']):
        category=categories[i%len(categories)]
        # category/zone deliberately somewhat mismatched so supply shortages are operationally meaningful.
        zone=zn[(i//3)%len(zn)]
        pref=['Morning,Afternoon','Afternoon,Evening','Morning,Evening'][(i//3)%3]
        partners.append(dict(partner_id=f'P{i+1:03d}',category=category,home_zone=zone,
                 shift_pattern=pref,flexible=int(i%4==0),weekly_day_off=i%7,
                 reliability=round(rng.uniform(.84,.97),3),completion_reliability=round(rng.uniform(.935,.985),3),
                 quality_score=round(rng.uniform(3.9,4.9),2),availability=round(rng.uniform(.78,.95),3),
                 source='existing',active_from_day=1))
    # Candidate onboarding pipeline demonstrates document vetting, assessment, training, capacity prioritization.
    candidates=[]
    for i in range(45):
        category=categories[(i*7+i//8)%3]
        zone=zn[(i*3+i//5)%8]
        score=55+int(rng.random()*46)
        bgcheck=1 if u01(seed,'bg',i)>.17 else 0
        trained=1 if u01(seed,'train',i)>.2 else 0
        status=('Ready' if bgcheck and trained and score>=73 else
                'Training required' if bgcheck and not trained else
                'Screening failed' if not bgcheck else 'Assessment below threshold')
        candidates.append(dict(candidate_id=f'C{i+1:03d}',category=category,zone=zone,
               acquisition_channel=['Community referral','Job fair','Digital outreach'][i%3],
               screening_score=score,identity_verified=bgcheck,training_passed=trained,
               status=status,eligible=int(status=='Ready'),
               readiness_day=ONBOARD_DAY+(i%4),
               reliability=round(rng.uniform(.89,.97),3),completion_reliability=round(rng.uniform(.95,.99),3),
               quality_score=round(rng.uniform(4.3,4.9),2),availability=round(rng.uniform(.81,.95),3),
               shift_pattern=['Morning,Afternoon','Afternoon,Evening','Morning,Evening'][i%3],
               weekly_day_off=i%7))
    return zdata,catdata,partners,candidates

def make_orders(seed,zdata,catdata,demand_mult=1):
    """Common demand tape for paired scenario comparisons, generated before dispatch."""
    rng=random.Random(seed+13011)
    orders=[]
    # Demand ~ 10 requests per zone/day; category allocation and peak shape are assumptions.
    slot_w={'Morning':1.02,'Afternoon':1.35,'Evening':1.50}
    ctr=0
    for d in range(1,DAYS+1):
        daydate=date(2026,9,1)+timedelta(days=d-1)
        weekend=1.22 if daydate.weekday()>=5 else 1
        for z in zdata:
            for c in catdata:
                for slot in SLOTS:
                    # Poisson via Knuth, no numpy dependency.
                    lam=.90*z['demand_index']*float(c['demand_multiplier'])*slot_w[slot]*weekend*demand_mult
                    p=math.exp(-lam);n=0;product=1.
                    while product>p:
                        n+=1;product*=rng.random()
                    qty=n-1
                    for _ in range(qty):
                        ctr+=1
                        orders.append(dict(order_id=f'O{ctr:06d}',day=d,date=daydate.isoformat(),
                            zone=z['zone'],category=c['category'],slot=slot,
                            model_booking_value_inr=int(c['model_booking_value_inr']),
                            priority='Urgent' if u01(seed,'urg',ctr)<.13 else 'Standard'))
    # priority order: urgent first, then timestamp proxy hash, deterministic for shared tape
    return sorted(orders,key=lambda o:(o['day'],SLOTS.index(o['slot']),o['priority']!='Urgent',u01(seed,'queue',o['order_id'])))

def plan_shortages(orders,partners):
    """Train ONLY on days 1..10; density gap proxy for onboarding & shift plans."""
    d=Counter((x['category'],x['zone']) for x in orders if x['day']<=HOLDOUT)
    supp=defaultdict(float)
    for p in partners:
        # expected slots active per day adjusted for day-off and availability
        supp[(p['category'],p['home_zone'])]+=2*(6/7)*p['availability']*HOLDOUT
    gap={key:d[key]/max(1.,supp[key]) for key in set(d)|set(supp)}
    return gap

def choose_candidates(orders,partners,candidates):
    pressure=plan_shortages(orders,partners)
    ready=[c for c in candidates if c['eligible']]
    # greedy targeted picks with diminishing benefit in oversubscribed zone/category
    count=Counter((p['category'],p['home_zone']) for p in partners)
    selected=[]
    for _ in range(min(ASSUMPTIONS['new_partners_selected'],len(ready))):
        best=max(ready,key=lambda c:(pressure.get((c['category'],c['zone']),0)/
                  (1+.25*sum(x['category']==c['category'] and x['zone']==c['zone'] for x in selected)),
                  c['screening_score'],c['candidate_id']))
        ready.remove(best);selected.append(best)
    return selected,pressure

def promote_candidates(selected):
    ps=[]
    for c in selected:
        ps.append(dict(partner_id='N'+c['candidate_id'][1:],category=c['category'],home_zone=c['zone'],
            shift_pattern=c['shift_pattern'],flexible=0,weekly_day_off=c['weekly_day_off'],
            reliability=c['reliability'],completion_reliability=c['completion_reliability'],
            quality_score=c['quality_score'],availability=c['availability'],source='onboarded',
            active_from_day=c['readiness_day']))
    return ps

def pick_shifts(orders,partners,seed):
    # Move 2-slot combinations only for voluntary, flexible existing professionals.
    # Forecast skill-zone category slot share from training tape days 1..10.
    demand=Counter((x['category'],x['zone'],x['slot']) for x in orders if x['day']<=HOLDOUT)
    decisions={};changed=[]
    for p in partners:
        orig=p['shift_pattern'].split(',')
        if not p['flexible'] or p['source']!='existing':continue
        best=sorted(SLOTS,key=lambda s:demand[(p['category'],p['home_zone'],s)],reverse=True)[:2]
        if set(best)!=set(orig):
            decisions[p['partner_id']]=','.join(s for s in SLOTS if s in best)
            changed.append({'partner_id':p['partner_id'],'category':p['category'],'zone':p['home_zone'],
                  'old_slots':p['shift_pattern'],'new_slots':decisions[p['partner_id']]})
    return decisions,changed

def simulate(orders,existing,selected,scenario,seed,availability_mult=1):
    pooling=scenario!='Baseline'; onboarding=scenario in ('Pooling + Onboarding','Quality-Safe Playbook','Peak-Shift Experiment')
    full=scenario=='Peak-Shift Experiment'
    coaching=scenario in ('Quality-Safe Playbook','Peak-Shift Experiment')
    partners=[dict(p) for p in existing]+(promote_candidates(selected) if onboarding else [])
    reassigned,changes=pick_shifts(orders,partners,seed) if full else ({},[])
    bycat=defaultdict(list)
    for p in partners:bycat[p['category']].append(p)
    assignments=defaultdict(int);availability_slots=Counter();observed_day_slots=set()
    job_count=Counter();rows=[]
    # Precompute availability slots for exact same partners and dates in all scenarios
    for d in range(HOLDOUT+1,DAYS+1):
        for p in partners:
            if d<p['active_from_day'] or ((d-1)%7)==p['weekly_day_off']:continue
            for slot in (reassigned.get(p['partner_id'],p['shift_pattern']).split(',')):
                if u01(seed,'avail',p['partner_id'],d,slot)<float(p['availability'])*availability_mult:
                    observed_day_slots.add((p['partner_id'],d,slot))
                    availability_slots[p['partner_id']]+=1
    for o in orders:
        if o['day']<=HOLDOUT:continue
        day=o['day'];slot=o['slot'];cat=o['category'];zone=o['zone'];oid=o['order_id']
        candidates=[]
        for p in bycat[cat]:
            home=p['home_zone']
            hop=0 if home==zone else (1 if pooling and home in EDGES[zone] else 99)
            if hop==99:continue
            pid=p['partner_id']
            if (pid,day,slot) not in observed_day_slots:continue
            if assignments[(pid,day,slot)] or job_count[(pid,day)]>=2:continue
            # nearest first, then more dependable, then seeded jitter; no ratings used as arbitrary exclusion
            score=hop*10+(1-float(p['reliability']))*8 +u01(seed,'rank',oid,pid)*.3
            candidates.append((score,p,hop))
        candidates.sort(key=lambda x:x[0])
        status='No supply';matched=None;hop=None
        for _,p,h in candidates[:3]:
            pid=p['partner_id']
            if u01(seed,'accept',oid,pid)<float(p['reliability']):
                assignments[(pid,day,slot)]=1;job_count[(pid,day)]+=1
                matched=p;hop=h;status='Completed';break
            status='Partner declined'
        travel=0;on_time=0;complaint=0;quality_rating=''
        if matched is not None:
            # CRN keyed order+partner, all scenarios use same counterfactual draws.
            pid=matched['partner_id']
            travel=int(15+20*hop+27*u01(seed,'travel',oid,pid))
            # No real-time transit; this is a proxy for whether the service would start promptly.
            cancel_p=1-float(matched['completion_reliability'])
            complaint_p=max(.018,min(.18,.16-(float(matched['quality_score'])-3.8)*.075))
            if coaching and matched['source']=='existing' and float(matched['quality_score'])<4.5:
                cancel_p*=1-ASSUMPTIONS['quality_coaching_cancellation_reduction_relative']
                complaint_p*=1-ASSUMPTIONS['quality_coaching_complaint_reduction_relative']
            if u01(seed,'cancel',oid,pid)<cancel_p:status='Partner cancellation'
            else:
                on_time=int(travel<=ASSUMPTIONS['on_time_eta_proxy_limit_minutes'])
                complaint=int(u01(seed,'complaint',oid,pid)<complaint_p)
                quality_rating=round(max(1,min(5,float(matched['quality_score'])-1.0*complaint +
                    (u01(seed,'rating',oid,pid)-.5)*.36)),2)
        rows.append(dict(order_id=oid,date=o['date'],day=day,zone=zone,category=cat,slot=slot,
              scenario=scenario,status=status,partner_id=matched['partner_id'] if matched else '',
              partner_origin=matched['source'] if matched else '',zone_hops=hop if hop is not None else '',
              travel_proxy_min=travel if matched else '',on_time=int(on_time),complaint=int(complaint),
              rating=quality_rating,booking_value_inr=o['model_booking_value_inr']))
    active=[p for p in partners if int(p['active_from_day'])<=DAYS]
    return rows,availability_slots,active,changes

def metrics(rows,slots,partners,scenario,selected,changes):
    n=len(rows);matched=[r for r in rows if r['partner_id']];completed=[r for r in rows if r['status']=='Completed']
    cancels=[r for r in rows if r['status']=='Partner cancellation']
    compl=sum(r['complaint'] for r in completed)
    ontime=sum(r['on_time'] for r in completed)
    bookings=sum(int(r['booking_value_inr']) for r in completed)
    onboarded_used={r['partner_id'] for r in matched if r['partner_origin']=='onboarded'}
    coached=[p for p in partners if p['source']=='existing' and float(p['quality_score'])<4.5]
    spend=(len(selected)*ASSUMPTIONS['onboarding_cost_inr_per_partner'] if scenario in SCENARIOS[2:] else 0)
    if scenario in SCENARIOS[3:]:
        spend+=len(coached)*ASSUMPTIONS['partner_coaching_cost_inr_each']+len(changes)*ASSUMPTIONS['peak_shift_coordination_cost_inr_each']
    # denominator booked *slots* only synthetic partner active capacity (not logged hours)
    use=sum(1 for r in matched)
    score={
     'scenario':scenario,'requests':n,'assigned':len(matched),'completed':len(completed),
     'fill_rate_pct':round(100*len(completed)/n,2) if n else 0,
     'assignment_rate_pct':round(100*len(matched)/n,2) if n else 0,
     'partner_cancellations':len(cancels),
     'cancellation_pct_of_assigned':round(100*len(cancels)/len(matched),2) if matched else 0,
     'on_time_pct_of_completed':round(100*ontime/len(completed),2) if completed else 0,
     'on_time_fulfillment_pct':round(100*ontime/n,2) if n else 0,
     'complaint_pct_of_completed':round(100*compl/len(completed),2) if completed else 0,
     'avg_rating':round(sum(float(r['rating']) for r in completed)/len(completed),3) if completed else 0,
     'completed_booking_value_proxy_inr':bookings,
     'unsupplied_requests':sum(1 for r in rows if r['status']=='No supply'),
     'partner_declined_requests':sum(1 for r in rows if r['status']=='Partner declined'),
     'partner_slots_available':sum(slots.values()),
     'partner_slot_utilization_pct':round(100*use/sum(slots.values()),2) if slots else 0,
     'partners_active_in_model':len(partners),
     'new_partners_selected':len(selected) if scenario in SCENARIOS[2:] else 0,
     'new_partners_used':len(onboarded_used),
     'coached_partners':len(coached) if scenario in SCENARIOS[3:] else 0,
     'flex_shift_changes':len(changes),
     'model_program_spend_inr':spend,
    }
    return score

def breakdown(rows,field):
    grp=defaultdict(list)
    for r in rows:grp[r[field]].append(r)
    out=[]
    for group,data in sorted(grp.items()):
        complete=[r for r in data if r['status']=='Completed']; m=[r for r in data if r['partner_id']]
        out.append(dict(dimension=field,group=group,requests=len(data),assigned=len(m),completed=len(complete),
             fill_rate_pct=round(100*len(complete)/len(data),2),
             on_time_pct=round(100*sum(r['on_time'] for r in complete)/len(complete),2) if complete else 0,
             on_time_fulfillment_pct=round(100*sum(r['on_time'] for r in complete)/len(data),2) if data else 0,
             complaint_pct=round(100*sum(r['complaint'] for r in complete)/len(complete),2) if complete else 0,
             cancel_pct=round(100*sum(r['status']=='Partner cancellation' for r in data)/len(m),2) if m else 0))
    return out

def run(seed=42,demand_mult=1,availability_mult=1,save=False):
    zdata,catdata,partners,candidates=get_inputs(seed)
    orders=make_orders(seed,zdata,catdata,demand_mult)
    selected,pressure=choose_candidates(orders,partners,candidates)
    all_rows=[];all_scores=[];detail=[];changes=[]
    for sc in SCENARIOS:
        res,slots,active,shift_changes=simulate(orders,partners,selected,sc,seed,availability_mult)
        all_rows.extend(res)
        all_scores.append(metrics(res,slots,active,sc,selected,shift_changes))
        for field in ('zone','category','slot'):
            for row in breakdown(res,field):detail.append(dict(scenario=sc,**row))
        if sc=='Peak-Shift Experiment':changes=shift_changes
    if save:
        DATA.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
        writecsv(DATA/'zones.csv',zdata);writecsv(DATA/'service_catalog.csv',catdata)
        writecsv(DATA/'existing_partners.csv',partners)
        writecsv(DATA/'onboarding_candidates.csv',candidates)
        writecsv(DATA/'synthetic_orders.csv',orders)
        writecsv(OUT/'order_outcomes.csv',all_rows)
        writecsv(OUT/'scenario_kpis.csv',all_scores)
        writecsv(OUT/'segment_kpis.csv',detail)
        writecsv(OUT/'targeted_onboarding_plan.csv',[
            dict(candidate_id=c['candidate_id'],category=c['category'],zone=c['zone'],screening_score=c['screening_score'],
                 verified=c['identity_verified'],training_passed=c['training_passed'],activation_day=c['readiness_day'],
                 training_pressure_index=round(pressure.get((c['category'],c['zone']),0),3),
                 next_action='Activate after final verification') for c in selected])
        writecsv(OUT/'shift_rebalancing_plan.csv',changes,cols=['partner_id','category','zone','old_slots','new_slots'])
        (DATA/'model_assumptions.json').write_text(json.dumps(ASSUMPTIONS,indent=2),encoding='utf-8')
        (OUT/'summary.json').write_text(json.dumps({'seed':seed,'scenario_kpis':all_scores,
          'scenario_segments':detail,'partner_coaching_rule':'existing quality score <4.5',
          'run_date_label':'synthetic Sep 2026','simulation_type':'counterfactual/illustrative',
          'selected_candidate_ids':[c['candidate_id'] for c in selected]},indent=2),encoding='utf-8')
    return {'kpis':all_scores,'segments':detail,'orders':len(orders),'selected':selected,'shift_changes':len(changes)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,default=42)
    ap.add_argument('--sensitivity',action='store_true');args=ap.parse_args()
    mainr=run(args.seed,save=True)
    print('Synthetic orders:',mainr['orders'],'New screened partners:',len(mainr['selected']))
    for k in mainr['kpis']:
        print(f"{k['scenario']:<24} fill {k['fill_rate_pct']:6.2f}%  completion {k['completed']:4d}  on-time {k['on_time_pct_of_completed']:5.1f}%  complaint {k['complaint_pct_of_completed']:5.2f}%")
    if args.sensitivity:
        sens=[]
        for name,dm,am in [('Normal',1,1),('Demand +15%',1.15,1),('Availability -10%',1,.9)]:
            for seed in [21,42,63,84,105]:
                r=run(seed,dm,am)
                for k in r['kpis']:
                    if k['scenario'] in ('Baseline','Quality-Safe Playbook'):
                        sens.append(dict(stress_test=name,seed=seed,demand_multiplier=dm,availability_multiplier=am,
                          scenario=k['scenario'],requests=k['requests'],completed=k['completed'],
                          fill_rate_pct=k['fill_rate_pct'],on_time_pct=k['on_time_pct_of_completed'],
                          complaint_pct=k['complaint_pct_of_completed']))
        writecsv(OUT/'sensitivity_runs.csv',sens)
        groups=defaultdict(list)
        for r in sens:groups[(r['stress_test'],r['scenario'])].append(r)
        agg=[]
        for (test,sc),rs in sorted(groups.items()):
            agg.append(dict(stress_test=test,scenario=sc,seeds=len(rs),
              avg_fill_rate_pct=round(sum(r['fill_rate_pct'] for r in rs)/len(rs),2),
              min_fill_rate_pct=min(r['fill_rate_pct'] for r in rs),
              max_fill_rate_pct=max(r['fill_rate_pct'] for r in rs),
              avg_on_time_pct=round(sum(r['on_time_pct'] for r in rs)/len(rs),2)))
        writecsv(OUT/'sensitivity_summary.csv',agg)
        print('Sensitivity summary:',agg)
if __name__=='__main__':main()
