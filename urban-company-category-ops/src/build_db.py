"""Create portable SQLite warehouse and SQL operational diagnostic export (standard library)."""
from pathlib import Path
import csv,sqlite3
ROOT=Path(__file__).resolve().parents[1]
TABLES={'orders':ROOT/'data/synthetic_orders.csv',
'existing_partners':ROOT/'data/existing_partners.csv',
'onboarding_candidates':ROOT/'data/onboarding_candidates.csv',
'outcomes':ROOT/'results/order_outcomes.csv',
'scenario_kpis':ROOT/'results/scenario_kpis.csv'}
DB=ROOT/'results/category_ops.sqlite'

def create():
    if DB.exists():DB.unlink()
    cx=sqlite3.connect(DB)
    for table,path in TABLES.items():
        with path.open(newline='',encoding='utf-8') as f:
            reader=csv.DictReader(f);cols=reader.fieldnames
            cx.execute(f'CREATE TABLE {table} ({", ".join(f"{k} TEXT" for k in cols)})')
            cx.executemany(f'INSERT INTO {table} VALUES ({",".join("?" for _ in cols)})',
                           ([row[k] for k in cols] for row in reader))
        cx.execute(f'CREATE INDEX idx_{table}_scenario ON {table} ({"scenario" if table in ("outcomes","scenario_kpis") else cols[0]})')
    cx.commit()
    sql=(ROOT/'sql/ops_diagnostics.sql').read_text(encoding='utf-8')
    # QUERY 1 is used for export. Other queries below are examples with their own terminators.
    query=sql.split('-- QUERY 1:')[-1].split('\n',1)[-1].split('-- QUERY 2:')[0].strip()
    cursor=cx.execute(query)
    with (ROOT/'results/sql_zone_category_diagnostics.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow([x[0] for x in cursor.description]);w.writerows(cursor.fetchall())
    print('SQL warehouse created:',DB)
    cx.close()
if __name__=='__main__':create()
