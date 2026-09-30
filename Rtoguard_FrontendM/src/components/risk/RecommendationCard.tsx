import {Link} from 'react-router-dom'
import {Play} from 'lucide-react'
import type {Recommendation} from '../../types'
import {ACTION_LABEL,inr} from '../../lib/format'
const Row=({l,children,c=''}:{l:string;children:React.ReactNode;c?:string})=><div className="flex justify-between border-b border-line py-2.5 last:border-0"><span className="text-t2">{l}</span><b className={`text-lg ${c}`}>{children}</b></div>
export default function RecommendationCard({r,simulateLink=true}:{r:Recommendation;simulateLink?:boolean}){
 return<div className="rounded-lg border border-brand bg-gradient-to-b from-brand/10 to-s1 p-5"><h2 className="font-semibold">Recommended Intervention</h2>
 <div className="my-2.5 text-[26px] font-semibold tracking-tight">{ACTION_LABEL[r.action].toUpperCase()}</div><p className="mb-3.5 text-t2">{r.rationale}</p>
 {r.suggestedDeposit>0&&<Row l="Suggested deposit">{inr(r.suggestedDeposit)}</Row>}
 <Row l="Expected RTO loss">{inr(r.lossBefore)} → {inr(r.lossAfter)}</Row><Row l="RTO loss avoided">{inr(r.rtoLossAvoided)}</Row><Row l="Intervention cost">− {inr(r.interventionCost)}</Row><Row l="Conversion-loss impact">− {inr(r.conversionLoss)}</Row><Row l="Net business impact" c={r.netImpact>=0?'text-lo':'text-hi'}>{inr(r.netImpact)}</Row>
 {simulateLink&&<Link to="/simulator" className="btn btn-p mt-4 w-full justify-center"><Play size={14}/>View 1,000-order Simulation</Link>}</div>}
