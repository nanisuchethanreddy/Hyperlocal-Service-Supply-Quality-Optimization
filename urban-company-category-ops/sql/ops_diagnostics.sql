-- SQL analytics using the generated SQLite database (src/build_db.py)
-- Explicit CAST because reproducible CSV importer stores values as text.
-- Synthetic data; not UC internal data.

-- QUERY 1: Zone-category heatmap of failure points in baseline vs recommended playbook
SELECT scenario, zone, category,
       COUNT(*) AS requests,
       SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed,
       ROUND(100.0*SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END)/COUNT(*),2) AS fill_rate_pct,
       SUM(CASE WHEN status='No supply' THEN 1 ELSE 0 END) AS unserved_no_supply,
       ROUND(100.0*SUM(CAST(on_time AS INTEGER))/COUNT(*),2) AS on_time_fulfillment_pct
FROM outcomes
WHERE scenario IN ('Baseline','Quality-Safe Playbook')
GROUP BY scenario,zone,category
ORDER BY scenario,fill_rate_pct ASC;

-- QUERY 2: Top capacity leak points in baseline (location + service + time of day)
SELECT zone,category,slot,COUNT(*) AS requests,
 SUM(CASE WHEN status='No supply' THEN 1 ELSE 0 END) AS no_supply,
 ROUND(100.0*SUM(CASE WHEN status='No supply' THEN 1 ELSE 0 END)/COUNT(*),2) AS no_supply_pct
FROM outcomes WHERE scenario='Baseline'
GROUP BY zone,category,slot HAVING COUNT(*)>=8
ORDER BY no_supply_pct DESC,requests DESC LIMIT 15;

-- QUERY 3: Synthetic candidate screening and training funnel
SELECT status,COUNT(*) AS candidates,
 ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM onboarding_candidates),1) AS candidate_share_pct
FROM onboarding_candidates GROUP BY status ORDER BY candidates DESC;

-- QUERY 4: Assigned-vs-on-time-fulfilled to avoid survivor-bias in punctuality KPIs
SELECT scenario,COUNT(*) AS requests,
 SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed,
 SUM(CAST(on_time AS INTEGER)) AS on_time_completed,
 ROUND(100.0*SUM(CAST(on_time AS INTEGER))/COUNT(*),2) AS on_time_fulfillment_pct,
 ROUND(100.0*SUM(CAST(on_time AS INTEGER))/NULLIF(SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END),0),2) AS on_time_pct_of_completed
FROM outcomes GROUP BY scenario ORDER BY on_time_fulfillment_pct DESC;

-- QUERY 5: Service-professional utilization proxy; jobs/available slots
-- True available slots come from scenario_kpis and are modeled, not observed.
SELECT scenario, COUNT(DISTINCT partner_id) AS partners_receiving_at_least_one_job,
 COUNT(*) AS assigned_jobs
FROM outcomes WHERE partner_id<>''
GROUP BY scenario ORDER BY assigned_jobs DESC;
