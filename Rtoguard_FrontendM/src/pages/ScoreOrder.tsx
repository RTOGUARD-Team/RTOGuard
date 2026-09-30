import {FormEvent,useState} from 'react'
import {Link} from 'react-router-dom'
import {useAsync} from '../hooks/useAsync'
import {useDemo} from '../hooks/useDemo'
import {getOperatorStates,persistenceNote,recordOutcome,scoreOrder,submitOperatorDecision} from '../services/api'
import {SCENARIOS} from '../data/demo'
import Panel,{PageTitle} from '../components/common/Panel'
import RiskScore from '../components/risk/RiskScore'
import RiskFactor from '../components/risk/RiskFactor'
import RecommendationCard from '../components/risk/RecommendationCard'
import DecisionPanel from '../components/risk/DecisionPanel'
import {ErrorState} from '../components/common/States'
import type {ScoreFeatures,Scored} from '../types'
export default function ScoreOrder(){const{demo}=useDemo(),[f,setF]=useState<ScoreFeatures>(SCENARIOS[2].features),[busy,setBusy]=useState(false),[err,setErr]=useState<Error>(),[res,setRes]=useState<Scored>(),op=useAsync(getOperatorStates,[demo])
 const set=<K extends keyof ScoreFeatures>(k:K,v:ScoreFeatures[K])=>setF({...f,[k]:v})
 const submit=async(e:FormEvent)=>{e.preventDefault();setBusy(true);setErr(undefined);try{const r=await scoreOrder(f);setRes(r);op.retry()}catch(x){setErr(x as Error);setRes(undefined)}finally{setBusy(false)}}
 const L=({t,children}:{t:string;children:React.ReactNode})=><div><label className="mb-1 block text-xs text-t2">{t}</label>{children}</div>
 const num=(k:'pastOrders'|'pastRtos'|'orderValue')=><input className="field" type="number" min={0} required value={f[k]} onChange={e=>set(k,+e.target.value)}/>
 return<><PageTitle title="Score New Order" sub="Submit order and customer context. The backend computes the risk score, factors, action and economics."/>
 <Panel className="mb-4"><div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-t3">Presets:{SCENARIOS.map(s=><button key={s.id} type="button" className="btn py-1 text-xs" onClick={()=>setF(s.features)}>{s.label}</button>)}</div>
 <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
 <L t="Customer type"><select className="field" value={f.customerType} onChange={e=>set('customerType',e.target.value as 'NEW'|'RETURNING')}><option value="NEW">New</option><option value="RETURNING">Returning</option></select></L>
 <L t="Past orders">{num('pastOrders')}</L><L t="Past RTOs">{num('pastRtos')}</L><L t="Order value (₹)">{num('orderValue')}</L>
 <L t="Payment mode"><select className="field" value={f.paymentMode} onChange={e=>set('paymentMode',e.target.value as 'COD'|'PREPAID')}><option>COD</option><option>PREPAID</option></select></L>
 <L t="Pincode"><input className="field" maxLength={6} value={f.pincode} onChange={e=>set('pincode',e.target.value)}/></L>
 <label className="flex items-end gap-2 pb-2 text-t2"><input type="checkbox" checked={f.festiveWindow} onChange={e=>set('festiveWindow',e.target.checked)}/>Festive window</label>
 <div className="flex items-end"><button className="btn btn-p w-full justify-center" disabled={busy}>{busy?'Scoring…':'Score Order'}</button></div></form>
 {demo&&<p className="mt-3 text-xs text-t3">Demo Mode replays the five saved scenarios. Turn it off to score any order on the backend.</p>}</Panel>
 {err&&<ErrorState title="Could not score this order" message={err.message}/>}
 {res&&<><p className="mb-3 text-t2">Saved as <b className="text-t1">{res.order.id}</b> in the decision queue. <Link className="text-brand underline" to="/dashboard">Open queue</Link></p><div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]"><div className="space-y-4"><Panel><RiskScore score={res.order.riskScore} level={res.order.riskLevel} loss={res.order.expectedLoss}/><p className="mt-3 text-xs text-t3">{res.modelNote}</p></Panel><Panel title="Why is this order risky?">{res.order.factors.map(x=><RiskFactor key={x.key} f={x}/>)}</Panel></div>
 <div className="space-y-4"><RecommendationCard r={res.recommendation}/><DecisionPanel key={res.order.id} orderId={res.order.id} riskScore={res.order.riskScore} action={res.recommendation.action} state={op.data?.[res.order.id]} note={persistenceNote()} onDecide={async d=>{await submitOperatorDecision(d);op.retry()}} onOutcome={async x=>{await recordOutcome(x);op.retry()}}/></div></div></>}</>}
