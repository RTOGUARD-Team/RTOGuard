import {useAsync} from '../hooks/useAsync'
import {useDemo} from '../hooks/useDemo'
import {getAnalytics,getEvaluation} from '../services/api'
import AsyncView from '../components/common/AsyncView'
import Disclosure from '../components/common/Disclosure'
import Panel,{PageTitle} from '../components/common/Panel'
import BarList from '../components/analytics/BarList'
import {ACTION_LABEL,dash,lakh,pct} from '../lib/format'
import type {Action} from '../types'
const M=({l,v,h}:{l:string;v:string;h?:string})=><div><div className="text-xs text-t3">{l}</div><b className="text-xl tabular-nums">{v}</b>{h&&<div className="text-xs text-t3">{h}</div>}</div>
export default function Analytics(){const{demo}=useDemo(),a=useAsync(getAnalytics,[demo]),e=useAsync(getEvaluation,[demo])
 return<><PageTitle title="Analytics" sub="Model evaluation from recorded outcomes, plus aggregates of the scored orders."/><Disclosure/>
 <AsyncView state={e}>{d=>{const m=[['synthetic outcomes',d.synthetic],['operator-recorded outcomes',d.operator]] as const
  return<Panel className="mb-4" title="Model evaluation" sub="High-risk = predicted HIGH · positive = actual RTO">{m.map(([n,x])=><div key={n} className="mb-4"><div className="mb-2 text-xs text-t2">Based on {x.n} {n}{n.startsWith('synthetic')&&' (synthetic, not observed)'}</div><div className="grid grid-cols-2 gap-4 sm:grid-cols-4"><M l="High-risk precision" v={dash(x.precision,pct)}/><M l="RTO recall" v={dash(x.recall,pct)}/><M l="False-positive rate" v={dash(x.fpr,pct)}/><M l="False-negative rate" v={dash(x.fnr,pct)}/></div></div>)}
  <div className="grid grid-cols-2 gap-4 border-t border-line pt-4 sm:grid-cols-4"><M l="Override rate" v={dash(d.overrideRate,pct)} h={`${d.decisions} decisions`}/><M l="Confirmation queue" v={String(d.queueVolume)} h="High-risk, awaiting review"/><M l="Avg decision latency" v={dash(d.avgLatencySec,v=>Math.round(v/60)+' min')}/></div><p className="mt-3 text-xs text-t3">{d.note}</p></Panel>}}</AsyncView>
 <AsyncView state={a}>{d=><div className="grid gap-4 lg:grid-cols-2">
 <Panel title="How does payment method affect RTO risk?" sub="Average predicted RTO probability"><BarList rows={d.rateByPayment} format={v=>v.toFixed(1)+'%'} color="#F59E0B"/></Panel>
 <Panel title="Where does expected loss concentrate?" sub="Baseline expected RTO loss by risk level"><BarList rows={d.lossByLevel} format={lakh} color="#EF4444"/></Panel>
 <Panel title="What is RTOGuard recommending?" sub="Orders per recommended action"><BarList rows={d.actions.map(x=>({...x,label:ACTION_LABEL[x.label as Action]??x.label}))} format={v=>v.toLocaleString('en-IN')}/></Panel></div>}</AsyncView></>}
