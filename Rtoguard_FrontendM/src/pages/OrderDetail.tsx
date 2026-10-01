import {useEffect} from 'react'
import {useParams} from 'react-router-dom'
import {useAsync} from '../hooks/useAsync'
import {useDemo} from '../hooks/useDemo'
import {getOperatorStates,getScored,persistenceNote,recordOutcome,submitOperatorDecision} from '../services/api'
import AsyncView from '../components/common/AsyncView'
import Panel,{PageTitle} from '../components/common/Panel'
import RiskScore from '../components/risk/RiskScore'
import RiskFactor from '../components/risk/RiskFactor'
import RecommendationCard from '../components/risk/RecommendationCard'
import DecisionPanel from '../components/risk/DecisionPanel'
import {EmptyState} from '../components/common/States'
import {inr} from '../lib/format'
export default function OrderDetail(){const{orderId=''}=useParams(),{demo,setOrderId}=useDemo()
 const s=useAsync(()=>getScored(orderId),[orderId,demo]),op=useAsync(getOperatorStates,[orderId,demo])
 useEffect(()=>{if(s.data)setOrderId(orderId)},[s.data,orderId,setOrderId])
 return<><PageTitle title="Order Risk Intelligence" sub="Predict the risk, explain the drivers, act, then record what actually happened."/>
 <AsyncView state={s}>{({order:o,recommendation:r,modelNote,state:orderState})=><><div className="mb-4 flex flex-wrap justify-between gap-4 rounded-lg border border-line bg-s1 p-[18px]">{[['Order ID',o.id],['Customer',o.customer],['Order value',inr(o.value)],['Location',o.location],['Payment',o.payment],['Order date',o.date]].map(([l,v])=><div key={l}><div className="text-xs text-t3">{l}</div><b>{v}</b></div>)}</div>
 <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]"><div className="space-y-4"><Panel><RiskScore score={o.riskScore} level={o.riskLevel} loss={o.expectedLoss}/><p className="mt-3 text-xs text-t3">{modelNote}</p></Panel><Panel title="Why is this order risky?" sub="Contribution of each factor to the score">{o.factors.length?o.factors.map(f=><RiskFactor key={f.key} f={f}/>):<EmptyState title="No risk factors returned" message="This order has no factor breakdown (batch orders carry only a score)."/>}</Panel></div>
 <div className="space-y-4"><RecommendationCard r={r}/><DecisionPanel key={orderId} orderId={o.id} riskScore={o.riskScore} action={r.action} state={orderState||op.data?.[o.id]} note={persistenceNote()} onDecide={async d=>{await submitOperatorDecision(d);s.retry();op.retry()}} onOutcome={async x=>{await recordOutcome(x);s.retry();op.retry()}}/></div></div></>}</AsyncView></>}
