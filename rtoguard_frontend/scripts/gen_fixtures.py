"""Regenerates src/data/fixtures.json (Demo Mode's synthetic data) by running the REAL backend engines.
Usage: python scripts/gen_fixtures.py /path/to/rtoguard-backend"""
import json, os, sys, tempfile
sys.path.insert(0, sys.argv[1]); os.environ["RTOGUARD_DB"] = os.path.join(tempfile.mkdtemp(), "f.db")
from app.api.mvp_routes import assumptions, evaluation, score_features
from app.api.rto_routes import simulation_engine as E
from app.services.festive import apply_festive
S = [('low','Low-risk order','ORD-1102','Meera Nair','Kochi, KL',dict(customer_type='RETURNING',past_orders=8,past_rtos=0,order_value=899,payment_mode='COD',pincode='682001')),
('medium','Medium-risk order','ORD-1077','Sana Khan','Hyderabad, TS',dict(customer_type='RETURNING',past_orders=4,past_rtos=1,order_value=1799,payment_mode='COD',pincode='500001')),
('high','High-risk order','ORD-1023','Rahul Sharma','Nagpur, MH',dict(customer_type='NEW',past_orders=0,past_rtos=0,order_value=2999,payment_mode='COD',pincode='226001')),
('hv-cod','High-value COD order','ORD-1058','Vikram Rao','Patna, BR',dict(customer_type='NEW',past_orders=0,past_rtos=0,order_value=8499,payment_mode='COD',pincode='800001')),
('repeat','Repeat-RTO customer','ORD-1090','Neha Joshi','Lucknow, UP',dict(customer_type='RETURNING',past_orders=6,past_rtos=3,order_value=1649,payment_mode='COD',pincode='226001'))]
o = E.generate_synthetic_orders(100, 42)
out = {'scenarios': [dict(scenarioId=i, label=l, orderId=oid, customer=c, location=loc, date='29 Sep 2026', features={**f, 'festive_window': False}, raw={**score_features({**f, 'festive_window': False}, oid), 'decision': None, 'outcome': None}) for i, l, oid, c, loc, f in S],
       'batch': E.simulate(o), 'batchFestive': {**E.simulate(apply_festive(o)), 'festive': True}, 'evaluation': evaluation(), 'assumptions': assumptions(100)}
json.dump(out, open('src/data/fixtures.json', 'w'), separators=(',', ':'))
print([(s['orderId'], s['raw']['risk_score'], s['raw']['risk_level'], s['raw']['recommended_action']) for s in out['scenarios']])
