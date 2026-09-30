import {useNavigate} from 'react-router-dom'
import {SCENARIOS} from '../../data/demo'
import {useDemo} from '../../hooks/useDemo'
export default function DemoModeSelector(){const{orderId,setOrderId}=useDemo(),nav=useNavigate(),cur=SCENARIOS.find(s=>s.orderId===orderId)
 return<select aria-label="Demo scenario" className="field w-auto" value={cur?.id??''} onChange={e=>{const s=SCENARIOS.find(x=>x.id===e.target.value);if(s){setOrderId(s.orderId);nav(`/orders/${s.orderId}`)}}}><option value="" disabled>Demo scenario…</option>{SCENARIOS.map(s=><option key={s.id} value={s.id}>{s.label}</option>)}</select>}
