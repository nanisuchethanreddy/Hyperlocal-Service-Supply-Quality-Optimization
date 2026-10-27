"""Create analysis documents and interview-ready artifacts from computed metrics."""
import json,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';D=ROOT/'docs';D.mkdir(exist_ok=True)
k=json.loads((R/'summary.json').read_text())['scenario_kpis']
by={v['scenario']:v for v in k};a=by['Baseline'];b=by['Quality-Safe Playbook'];c=by['Pooling + Onboarding'];d=by['Peak-Shift Experiment']
diff=lambda field:round(b[field]-a[field],2)
spend=b['model_program_spend_inr'];incremental=b['completed']-a['completed']
per=spend/incremental
kpi='\n'.join(f"| {x['scenario']} | {x['completed']:,} | {x['fill_rate_pct']:.2f}% | {x['on_time_fulfillment_pct']:.2f}% | {x['on_time_pct_of_completed']:.2f}% | {x['complaint_pct_of_completed']:.2f}% | ₹{x['model_program_spend_inr']:,} |" for x in k)
readme=f'''# Hyperlocal Service Supply & Quality Optimization — Independent Case Study

> **Portfolio project for Category Manager / Business Operations roles.** A fully reproducible, synthetic marketplace simulation inspired by public home-services categories and the user-provided job description. **Not affiliated with, commissioned by, or powered by private Urban Company data.** All numeric results are MODEL ESTIMATES and should never be represented as real-world company outcomes.

![Dashboard preview](dashboard/dashboard_preview.png)

## Executive result

- **City modeled:** Hyderabad; 8 illustrative micro-markets, 3 verified public service lines (AC Repair, Bathroom Cleaning, Electrician)
- **Study:** September 1–28, 2026 (synthetic); **{len({r['scenario'] for r in k})} scenarios**; 10 planning days + 18-day evaluation holdout; **{a['requests']:,} held-out requests** from **{sum(int(x['requests']) for x in k[:1])+0}**? holdout only; complete dataset in `data/synthetic_orders.csv`
- **Partner cohorts:** 96 existing synthetic partners, 45 candidate profiles, 12 screened selections
- **Recommended:** `Quality-Safe Playbook` = one-hop pooling + qualified onboarding + assumed effectiveness of quality coaching (not a proven causal result)
- **Completed requests:** {a['completed']:,} → {b['completed']:,} (**+{incremental:,}**)
- **Fill rate:** {a['fill_rate_pct']:.2f}% → {b['fill_rate_pct']:.2f}% (**+{diff('fill_rate_pct'):.2f} percentage points**)
- **On-time fulfillment across ALL requests:** {a['on_time_fulfillment_pct']:.2f}% → {b['on_time_fulfillment_pct']:.2f}% (**+{diff('on_time_fulfillment_pct'):.2f} pp**)
- **Complaint rate of completed requests:** {a['complaint_pct_of_completed']:.2f}% → {b['complaint_pct_of_completed']:.2f}%; training impacts are ASSUMED, not field-validated.
- **Illustrative program spend:** ₹{spend:,}; **₹{per:.2f} cost per incremental completed request** across this 18-day simulation, not actual incremental contribution margin or realized ROI.

**Important caveat:** Baseline's conditional on-time rate is 100% because it dispatches only within each home zone and all modeled local trips fit the illustrative 45-minute threshold. That does *not* mean 100% of customer requests were served on time. Using all requests as the denominator reveals the correct {a['on_time_fulfillment_pct']:.2f}% baseline. Cross-zone pooling improves availability but can increase late arrivals among completed bookings.

## Files

| Path | Contents |
|---|---|
| `src/simulate.py` | Standard-library synthetic demand generation, partner matching, screening, policy experiments, stress tests |
| `src/build_db.py` + `sql/ops_diagnostics.sql` | SQLite warehouse, 5 auditable operations queries |
| `src/build_html.py` | Offline interactive HTML with scenario, locality, category and time-slot filters |
| `src/build_workbook.py` | Excel workbook builder using optional `artifact_tool` dependency |
| `src/build_brief.py` | PDF leadership brief builder using `reportlab` |
| `data/` | Reproducible input master data and illustrative assumptions |
| `results/` | Detailed order outcomes, scenario metrics, segmentation, onboarding/shift plan, stress runs, SQLite DB |
| `dashboard/interactive_dashboard.html` | Open directly in any modern browser (no server, CDN or login) |
| `dashboard/Category_Operations_Dashboard.xlsx` | 7-sheet Excel scorecard and operational drilldown |
| `reports/Management_Brief.pdf` | Two-page decision brief |
| `docs/` | Case study, data dictionary, SOPs, interview narration, public-source provenance |
| `tests/` | Integrity and determinism checks |

## Run from a clean clone

Requires **Python 3.10+**. Core simulation, HTML dashboard, and SQLite require **no third-party Python packages**.

```bash
python src/simulate.py --seed 42 --sensitivity
python -m unittest discover -s tests -v
python src/build_db.py
python src/build_html.py
```

The packaged Excel and PDF are ready to open. Rebuild them in the creation environment with the optional dependencies:

```bash
# optional, if artifact_tool is available in your Python environment
python src/build_workbook.py
# optional, after installing reportlab
python src/build_brief.py
```

Sensitivity uses seeds 21, 42, 63, 84, 105; request arrivals, partner availability and customer outcomes are deterministic for each seed. The planning algorithm uses **days 1–10 only** and evaluates recommendations on **days 11–28**, preventing same-period demand information from entering the intervention choice. The scenarios are paired on identical demand tapes per seed.

## Comparison on the held-out evaluation window

| Policy | Completed | Fill rate | On-time / all requests | On-time / completed | Complaints / completed | Illustrative spend |
|---|---:|---:|---:|---:|---:|---:|
{kpi}

**Interpretation:** `Quality-Safe Playbook` provides a defensible illustrative balance of fulfillment, service reliability and complaint control. `Peak-Shift Experiment` changes flexible partner two-slot schedules without increasing daily slots, but worsens overall on-time fulfillment vs the quality-safe alternative in this sample; do not claim that reshuffling helped without validation.

## Core decision logic

1. Generate service requests from declared assumptions for day × zone × category × slot, with seeded Poisson demand and weekend variation.
2. Generate synthetic partner pools with service skill, home zone, schedule, weekly rest day, acceptance probability, completion reliability and training/quality values.
3. During planning days 1–10, estimate shortage pressure = observed demand / expected local available slot capacity by category × zone.
4. Select 12 **verified, training-passed** candidate profiles, ranked by shortage pressure and a diminishing-return term. Activate only after their modeled readiness day.
5. Dispatch each held-out request to up to 3 eligible professionals with free capacity, matching service category, day/slot availability and local/adjacent zone policy.
6. Simulate willingness to accept, cancellations, 45-minute on-time travel proxy and complaint risk. Baseline, pooling, onboarding, coaching and peak-shift policies share demand tape and seeded outcomes.
7. Compare five scenarios across booked fulfillment, on-time completion over all requests, complaints, cost per incremental completion, supply availability, and capacity utilization.
8. Stress-test a 15% demand surge and a 10% partner availability decline, across five independent deterministic seeds. These are robustness checks, NOT confidence intervals or live A/B tests.

## Limitations and business safety

- Synthetic requests, demographics-free IDs, travel times, service durations, candidate assessments, ratings and financial assumptions; no scraped customer information.
- Hyderabad locality names are recognizable, but zone links are an **illustrative network**; model travel proxy is not estimated from roads or maps.
- Demand/cancellation/acceptance distributions are **not calibrated** to Urban Company's internal data. Service price proxies and onboarding/coaching costs are NOT Urban Company pricing or fee information.
- Model does not explicitly measure provider wages, out-of-pocket travel expenses, autonomy, satisfaction, churn, customer refunds, partner payout or equity. Never deploy policies without partner consent, welfare safeguards, verified service qualification and direct field observation.
- One deterministic seed is a demonstration, not statistical proof. Five seed sensitivity ranges are a diagnostic only.
- The simulated coaching effectiveness is an input assumption. **No causal effect of training has been demonstrated.**

## Public context / provenance

- Urban Company, public Hyderabad services page: https://www.urbancompany.com/Hyderabad (used to verify modeled service categories; *not* to infer volumes or prices).
- Urban Company Investor Relations, Service Professional Enablement, 28 June 2024: https://investorrelations.urbancompany.com/announcements-and-highlights/service-professional-enablement (operating context: partner training/quality, fulfillment and flexibility; not model calibration).
- Campus job description supplied by user: `Campus Category Manager (Business Operations).pdf`, page 2 (scope: quality supply onboarding, city operations and growth/quality initiatives). Not redistributed to respect ownership.

For model rules see `docs/methodology.md`, operational rollout plan `docs/operating_sop.md` and interview answers `docs/interview_walkthrough.md`.
'''
# replace accidental awkward interpolation with explicit total generated orders read from CSV
with (ROOT/'data/synthetic_orders.csv').open(newline='',encoding='utf-8') as f:
    total=sum(1 for _ in csv.DictReader(f))
readme=readme.replace(f"**{a['requests']:,} held-out requests** from **{sum(int(x['requests']) for x in k[:1])+0}**? holdout only",f"**{a['requests']:,} held-out requests** from **{total:,} generated requests across 28 days**")
(ROOT/'README.md').write_text(readme,encoding='utf-8')

(D/'methodology.md').write_text(f'''# Methodology, operational design, and metrics

## Objective
Maximize **quality-adjusted fulfilled demand**, subject to matching category skills, partner consent/availability, no double booking, maximum two shifts per day, geographic reach, and service quality. This is a medium-complexity teaching simulation, not an operational solver for Urban Company's systems.

## Structured business question
*Given uneven demand across eight Hyderabad illustrative service zones, which combination of local matching, one-hop partner pooling, qualified onboarding and partner coaching maximizes the number of on-time fulfilled home-service requests without excessive quality deterioration?*

## Data generation
- Dates: 1–28 September 2026, 28 days.
- Services: AC Repair, Bathroom Cleaning, Electrician. The public listing verifies **category existence only**.
- Base demand uses seeded Poisson distribution: `lambda = 0.90 × zone_demand_index × category_index × slot_index × weekend_multiplier × stress_multiplier`. All factors are manually assumed; check `src/simulate.py`.
- Morning, afternoon, evening are four-hour modeled slots; each partner is assigned two daily slots and is off once weekly.
- Existing partners: 96 synthetic professionals balanced across zone-category cells. Availability, acceptance, completion, complaint tendencies are randomly generated within explicitly coded ranges.
- Candidate funnel: 45 synthetic people; candidate must have verified identity, passed training, screening score >= 73. The final selection uses a shortage-pressure proxy and diminishing returns; 12 are selected.

## Train-holdout design
- Planning data: days 1–10; shortage pressure derived only here.
- Test data: days 11–28; ALL reported main KPIs use these 18 days.
- New partners active from day 13 to 16, if selected and verified.
- Scenario outcomes use common demand tapes and hash-stable pseudo-random draws. No future demand features enter planning. This is controlled simulation, not causal evidence.

## Scenarios

1. **Baseline:** Assign only from same service category and same home zone.
2. **Zone Pooling:** Allow local first, then illustrative adjacent microzones.
3. **Pooling + Onboarding:** Add 12 vetted partners to high shortage-pressure cells, after readiness dates.
4. **Quality-Safe Playbook (recommended for pilot):** Pooling + onboarding plus an **assumed 22% relative partner-cancellation reduction and 25% relative complaint reduction** for coached existing professionals with synthetic quality score <4.5.
5. **Peak-Shift Experiment:** Same policies plus a forecast-driven swap of voluntary flexible professionals into two highest-demand slots, **still only two slots per partner**. Included as a transparent negative/neutral result.

## Dispatch
Eligible professionals: category match; booked slots/day capacity available; schedule covers service slot; not on modeled rest day; current day >= activation date. Accept/reject offers independently using partner-specific simulated probability. If first three offers decline or capacity absent, order remains unfulfilled. On acceptance, simulate post-booking cancellation, travel proxy and complaint. Partner is not assigned to overlapping requests in one slot; max two slots/day.

## Definitions

| Metric | Definition | Why it matters |
|---|---|---|
| Booking fill rate | completed / all requests × 100 | Captures actual customer demand served, not merely assignment |
| Assignment rate | assigned / all requests × 100 | Upper bound on completions; cancellations still possible |
| On-time fulfillment | completed & travel_proxy <=45 / all requests × 100 | Combines coverage and responsiveness; no survivor bias |
| Conditional on-time rate | completed on-time / all completed × 100 | Useful only alongside demand coverage |
| Complaint rate | completed bookings with simulated complaint / all completed × 100 | Quality signal, simulated not observed |
| Partner cancellation rate | partner-cancelled bookings / assigned bookings × 100 | Completion reliability |
| Partner slot utilization | assigned bookings / simulated available partner slots × 100 | Capacity consumption proxy; not paid-hours utilization |
| Spend/incremental completion | illustrative intervention spend / (scenario completions − baseline completions) | A cost-effectiveness proxy, **not** profit, partner earnings or ROI |

### Reference results (seed 42, holdout only)

- Booking fill: {a['fill_rate_pct']:.2f}% to {b['fill_rate_pct']:.2f}% (**+{diff('fill_rate_pct'):.2f} pp**), {incremental} incremental completed requests.
- On-time fulfillment: {a['on_time_fulfillment_pct']:.2f}% to {b['on_time_fulfillment_pct']:.2f}% (**+{diff('on_time_fulfillment_pct'):.2f} pp**).
- Complaints: {a['complaint_pct_of_completed']:.2f}% to {b['complaint_pct_of_completed']:.2f}% (−{a['complaint_pct_of_completed']-b['complaint_pct_of_completed']:.2f} pp).
- Program spend assumption: ₹{spend:,}; implied spend per incremental completed booking: ₹{per:.2f}.
- Pooling-only conditional on-time is worse than baseline. Peak-shift variant is not dominant; scenario ranking depends on safety constraints and value assigned to customer punctuality and professional welfare.

## How to verify

```bash
python src/simulate.py --seed 42 --sensitivity
python -m unittest discover -s tests -v
python src/build_db.py
```

Independent audit checks include deterministic orders, no double booking, active date checks, training gates, count identities, and constant scheduled capacity under shift rebalancing.

## Follow-up if company data becomes available
Replace illustrative with aggregated, privacy-safe, consented: 8-week zone-hour requests, service category, accepted/missed/rescheduled bookings, true ETAs, verified training records, opt-in work hours, partner pay/travel expenses and audited complaints. Recalibrate assumptions, benchmark simple baseline, run prospective limited pilots with safety guardrails; do not use individual sensitive records in public GitHub.
''',encoding='utf-8')

(D/'operating_sop.md').write_text('''# Category Manager field execution SOP (proposed, not official policy)

## 1. Daily operating cadence

**08:30 – Supply health.** Review next-day demand by service-zone-slot; flagged >15% capacity shortages, cancellations, backlog and supply opt-in availability. Contact consenting existing partners about voluntary extra availability; do not coerce shift changes.

**11:00 – Partner onboarding.** Screen candidates (IDs/certifications where legally appropriate), interview and skills assessment, shadowing/approved safety training and readiness confirmation. Document fail reasons without exposing sensitive personal data.

**14:00 – Quality and incident review.** Audit unresolved complaints and reschedules; distinguish training needs from system issues, missing tools, unreasonable travel, or unfair assignment. Escalate safety incidents to appropriate qualified teams.

**17:00 – Peak service response.** If local capacity short, check one-hop partner consent and safe travel ETA, then broaden pooling cautiously. Do not sacrifice worker welfare or promise punctuality based on proxy travel alone.

**19:30 – KPI closure.** Share requests, assignment, completion, on-time/request, complaint %, cancellation %, professional opt-in utilization, unserved orders and root causes by zone/category.

## 2. Proposed partner onboarding checklist

- Verify required credentials and trade capability through approved processes.
- Confirm training outcome, available service scope, and kit/tools readiness.
- Explain transparent service standards and customer communication, plus partner autonomy and expected travel.
- Run supervised quality assessment; do not activate if a legally required check or training is incomplete.
- Assign an onboarding owner and audit first few completed orders with consent and privacy controls.

## 3. Decision thresholds (illustrative and configurable)

| Trigger (illustrative) | Action | Escalation |
|---|---|---|
| Demand/service-zone forecast exceeds partner opt-in capacity by >15% | Request optional neighboring availability; increase lead pipeline | City category owner |
| All-request on-time fulfillment <80% | Diagnose unserved requests versus late cross-zone starts | Ops manager |
| Complaint percentage increases >1 pp week-on-week | Category complaint root-cause review and partner support | Quality team |
| Peak-shift trial harms on-time fulfillment or partner feedback | Stop trial, restore opt-in schedules | City head |
| Safety incident or verified qualification issue | Halt affected service assignment pending authorized review | Safety / compliance |

These are pilot thresholds chosen for the portfolio project, not official UC policies or published SLAs.

## 4. Responsible deployment gates

Pilot requires true road ETAs, consented opt-in hours, professional earnings/travel burden analysis, privacy-safe operational data, service safety verification, and prospective customer quality tracking. Evidence from this simulation alone cannot justify real partner penalties or changes to compensation.
''',encoding='utf-8')

(D/'interview_walkthrough.md').write_text(f'''# Interview script and defendable project answers

## 60-second project explanation

> I completed an independent operations analytics project inspired by the responsibilities of a home-services Category Manager. I modeled three service categories across eight illustrative Hyderabad zones over 28 synthetic days. I generated demand and a professional onboarding funnel, then simulated partner matching and service quality under five operational policies. I used the first 10 days for planning and evaluated each approach on the same 18-day held-out demand. The best quality-balanced scenario increased simulated completion from {a['fill_rate_pct']:.1f}% to {b['fill_rate_pct']:.1f}%—a {diff('fill_rate_pct'):.1f}-percentage-point gain—while improving on-time fulfillment across all requests by {diff('on_time_fulfillment_pct'):.1f} points. I also found that wider geographic pooling harms punctuality among the customers it serves, and an extra peak-shift policy did not outperform the safer alternative. This was synthetic analysis, not real Urban Company performance.

## Most important interviewer questions

**Q1: Was this a real operational project?** No. It is a fully simulated case study. Public sources only established service-category and operations context. The full code, assumptions, seeded input and output CSVs are included.

**Q2: Why Hyderabad and these categories?** Hyderabad is a real UC service city; AC Repair, Bathroom Cleaning and electrician services appear in the official public catalog. The specific modeled zone adjacency, staffing and requests are assumptions.

**Q3: What exactly did you do yourself?** Developed the generator, candidate assessment gate, shortage-pressure planning rule, capacity-constrained partner assignment, scenario scoring and quality/cost KPI definitions; implemented repeatable tests, SQL diagnostics, interactive HTML dashboard, and Excel reports.

**Q4: What was the root-cause problem?** Local supply did not align with category/zone/slot demand. Baseline served {a['completed']} of {a['requests']} holdout requests. Pooling unlocked spare adjacent supply but at the expense of some travel punctuality.

**Q5: Why not just add as many partners as possible?** More partners impose recruiting and coaching costs, risk overcapacity, and may reduce professionals' opportunity to earn. The project targets screened candidates in demand-constrained cells and tracks partner availability, but cannot measure actual earnings. Any pilot must add that safeguard.

**Q6: What is your main recommendation?** Pilot targeted one-hop pooling and qualified supply recruitment with quality coaching. Use actual travel-time promises and professional welfare guardrails, instead of treating this simulation as proof.

**Q7: Why show on-time fulfillment on all requests?** Conditional punctuality can be misleading when only easy nearby jobs are served. Baseline is 100% on time *among completions*, while 29.9% of requests never complete. The all-request measure captures real customer coverage.

**Q8: How does the model measure profit?** It does not. It has an illustrative intervention-spend proxy only. No actual commissions, margins, payouts, or contribution are measured, and no ROI claim is justified.

**Q9: Why are you calling onboarding quality improvements assumptions?** Coaching affects cancellations and complaints according to two openly coded effectiveness factors; without field controls, we cannot attribute measured real-world effects.

**Q10: What is an unexpected result?** Peak-shift experiments reduced aggregate on-time fulfillment from {b['on_time_fulfillment_pct']:.2f}% to {d['on_time_fulfillment_pct']:.2f}% in the fixed example while spending more. I would not recommend rolling out the shift-change policy without a controlled pilot.

## Honest resume presentation

Always introduce figures as **simulated / synthetic / modeled**. Describe outcomes in percentage points, not vague percentages. You can discuss stakeholder/SOP recommendations, but do not claim direct service-professional recruitment or implemented changes to Urban Company's marketplace.
''',encoding='utf-8')

(D/'data_dictionary.md').write_text('''# Data dictionary and audit trail

| CSV | Grain / key | Relevant columns |
|---|---|---|
| `data/zones.csv` | one per assumed operational zone | zone, demand_index, cluster, adjacent_zones |
| `data/service_catalog.csv` | one per modeled service | category, demand_multiplier, model_booking_value_inr |
| `data/existing_partners.csv` | one per synthetic existing professional | partner_id, category, home_zone, shift_pattern, flexible, weekly_day_off, reliability, availability, active_from_day |
| `data/onboarding_candidates.csv` | one per modeled candidate | candidate_id, category, zone, screening_score, identity_verified, training_passed, eligible, readiness_day |
| `data/synthetic_orders.csv` | one per generated booking request | order_id, day, date, zone, category, slot, model_booking_value_inr, priority |
| `results/order_outcomes.csv` | one order × one scenario in held-out 18 days | order_id, date, day, zone, category, scenario, status, partner_id, on_time, complaint, travel_proxy_min, rating |
| `results/scenario_kpis.csv` | one row per policy | requested, assigned, completed, fill_rate_pct, on_time_fulfillment_pct, complaint_pct_of_completed, model_program_spend_inr |
| `results/segment_kpis.csv` | one policy × dimension × group | scenario, dimension, group, requests, completed, fill_rate_pct, on_time_fulfillment_pct, complaint_pct |
| `results/targeted_onboarding_plan.csv` | 12 shortlisted candidates | candidate_id, zone, category, training_pressure_index, activation_day |
| `results/shift_rebalancing_plan.csv` | moved flexible professional slot pair | partner_id, old_slots, new_slots |
| `results/sensitivity_runs.csv` | stress × seed × 2 policies | seed, requests, fill_rate_pct, on_time_pct |
| `results/sensitivity_summary.csv` | stress × 2 policies | average/min/max of five seeds |
| `results/sql_zone_category_diagnostics.csv` | policy × zone × category | SQL-derived requests, completed, on_time_fulfillment_pct |
| `results/category_ops.sqlite` | SQLite operational warehouse | orders, existing_partners, onboarding_candidates, outcomes, scenario_kpis |

**Unit definitions:** `on_time` is Boolean (1/0). `complaint` is Boolean (1/0). `zone_hops` is illustrative topology depth (0 or 1). `travel_proxy_min` is synthetic minutes, never actual map ETA. Values named `_inr` are proxy assumptions, not company financials. Scenario KPI rates are stored as percentages (70.13 means 70.13%, not 0.7013). Empty matching partner denotes unassigned request. IDs are random aliases with no personal information.

**Status meanings:** `No supply` = no eligible available partner; `Partner declined` = partner offers declined; `Partner cancellation` = assigned but later not completed; `Completed` = served. All missing orders are explicitly in the output, not filtered away.
''',encoding='utf-8')

(D/'sources.md').write_text('''# Public information vs synthetic model assumptions

## Verified contextual sources

1. [Urban Company public Hyderabad services catalog](https://www.urbancompany.com/Hyderabad) — presence of AC repair/service, bathroom cleaning, electricians; accessed October 2026. Used ONLY to select category names and broad marketplace framing. Listed consumer prices are NOT used for this model.
2. [Urban Company Investor Relations: Service Professional Enablement](https://investorrelations.urbancompany.com/announcements-and-highlights/service-professional-enablement), June 28, 2024. Supports the importance of professional training/upskilling, quality standards, service fulfillment and balanced partner flexibility. Historical public context, not a calibration dataset.
3. `Campus Category Manager (Business Operations).pdf`, provided by project requester, page 2, includes supply onboarding, daily city operations, growth/quality, analytical problem-solving and SOP expectations. Not included in repository to avoid redistributing a user-provided document.

## Entirely illustrative and not traceable to Urban Company

- All simulated request volumes and distribution parameters, partner headcount, worker-level records, scheduling availability, acceptance/quality probabilities, partner training assessments and performance metrics.
- Selected neighborhoods used as recognizable labels; their adjacency is a fictionalized operating-topology proxy. These are not official UC boundaries or travel routes.
- Program costs, booked value proxies, travel times, 45-minute threshold and training effectiveness scenarios.
- Revenue/GMV proxy is completed service value under *illustrative category ticket values*, not measured bookings, platform commission, partner payout, revenue, margin or net profit.

No proprietary booking, earnings, customer, contractor or company data were obtained or claimed.
''',encoding='utf-8')

bullets=f'''PROJECT: Hyperlocal Service Supply & Quality Optimization | Independent Synthetic Case Study
Tools: Python, Excel, SQLite/SQL, HTML/JavaScript | Hyderabad (illustrative)

• Built a 28-day synthetic home-services operations model across 8 Hyderabad microzones and 3 service categories, generating {total:,} requests and modeling 96 service professionals plus a 45-candidate onboarding funnel.
• Developed capacity-constrained partner dispatch, shortage-pressure forecasting, and verified-candidate screening; evaluated 5 policies on a separate 18-day holdout using reproducible Python and SQL.
• Improved **simulated** booking fill from {a['fill_rate_pct']:.1f}% to {b['fill_rate_pct']:.1f}% (+{diff('fill_rate_pct'):.1f} pp; +{incremental:,} completed services) through one-hop supply pooling, 12 qualified additions and assumed quality coaching.
• Increased **modeled** on-time fulfillment across all requests by {diff('on_time_fulfillment_pct'):.1f} pp; built 7-sheet Excel and interactive dashboards, quality/SOP recommendations and five-seed demand/availability stress tests.

Important: ALL metrics are synthetic counterfactuals. No Urban Company operations, workers or revenue were directly studied.
'''
(ROOT/'reports/resume_bullets.txt').write_text(bullets,encoding='utf-8')
(ROOT/'.gitignore').write_text('__pycache__/\n*.pyc\n.DS_Store\n.vscode/\n.ipynb_checkpoints/\n',encoding='utf-8')
(ROOT/'LICENSE').write_text('MIT License\n\nCopyright (c) 2026 Independent portfolio project author\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n',encoding='utf-8')
print('Created README + methodology/SOP/interview/data-dictionary/sources + resume bullets',total)
