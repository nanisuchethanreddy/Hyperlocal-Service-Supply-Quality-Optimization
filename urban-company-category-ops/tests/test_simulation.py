"""Run with: python -m unittest discover -s tests -v"""
import sys, unittest
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import simulate as sim
class TestSyntheticMarket(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.z,cls.c,cls.p,cls.candidates=sim.get_inputs(42)
        cls.orders=sim.make_orders(42,cls.z,cls.c)
        cls.selected, cls.shortage=sim.choose_candidates(cls.orders,cls.p,cls.candidates)
    def test_deterministic_replay(self):
        self.assertEqual(self.orders,sim.make_orders(42,self.z,self.c))
        self.assertEqual([p['candidate_id'] for p in self.selected],
                         [p['candidate_id'] for p in sim.choose_candidates(self.orders,self.p,self.candidates)[0]])
    def test_supply_integrity(self):
        self.assertEqual(len(self.p),96)
        self.assertEqual(len(set(p['partner_id'] for p in self.p)),96)
        self.assertTrue(all(p['category'] in [c[0] for c in sim.CATS] for p in self.p))
    def test_screening_gate(self):
        self.assertEqual(len(self.selected),12)
        self.assertTrue(all(c['identity_verified'] and c['training_passed'] and c['screening_score']>=73 for c in self.selected))
        self.assertTrue(all(c['readiness_day']>=sim.ONBOARD_DAY for c in self.selected))
    def test_no_double_booking_and_holdout(self):
        rows,_,_,_=sim.simulate(self.orders,self.p,self.selected,'Quality-Safe Playbook',42)
        keyed=Counter((r['partner_id'],r['day'],r['slot']) for r in rows if r['partner_id'])
        self.assertTrue(all(k<=1 for k in keyed.values()))
        keyed_day=Counter((r['partner_id'],r['day']) for r in rows if r['partner_id'])
        self.assertTrue(all(k<=2 for k in keyed_day.values()))
        self.assertTrue(all(r['day']>sim.HOLDOUT for r in rows))
        self.assertTrue(all(r['day']>=sim.ONBOARD_DAY for r in rows if r['partner_origin']=='onboarded'))
    def test_kpi_internal_consistency(self):
        for sc in sim.SCENARIOS:
            rows,slots,partners,changes=sim.simulate(self.orders,self.p,self.selected,sc,42)
            k=sim.metrics(rows,slots,partners,sc,self.selected,changes)
            self.assertTrue(k['completed']<=k['assigned']<=k['requests'])
            self.assertEqual(k['assigned'],k['completed']+k['partner_cancellations'])
            self.assertEqual(k['requests'],k['completed']+k['partner_cancellations']+k['unsupplied_requests']+k['partner_declined_requests'])
            self.assertTrue(k['on_time_fulfillment_pct']<=k['fill_rate_pct'])
    def test_slot_rebalancing_preserves_total_shift_capacity(self):
        decision,changes=sim.pick_shifts(self.orders,self.p,42)
        for p in self.p:
            self.assertEqual(len(p['shift_pattern'].split(',')),2)
            self.assertEqual(len(decision.get(p['partner_id'],p['shift_pattern']).split(',')),2)
        self.assertEqual(len(changes),len(decision))
if __name__=='__main__':unittest.main()
