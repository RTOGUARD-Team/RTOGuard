/**
 * The ONLY module that talks to a data source.
 *   Demo Mode ON  -> saved synthetic output of the real backend engines (src/data/fixtures.json) + browser storage for decisions
 *   Demo Mode OFF -> FastAPI. Scoring, economics, decisions, outcomes, evaluation and festive all live in the backend.
 * Base URL: VITE_API_BASE_URL (empty = same origin; vite.config.ts proxies /rto and /api to :8000).
 * snake_case -> UI types happens only in the mappers below.
 */
import type {AnalyticsData,AssumptionItem,DashboardMetrics,DecisionEvent,Evaluation,OperatorState,Order,OutcomeRecord,Recommendation,RiskAssessment,RiskFactor,RiskLevel,ScoreFeatures,Scored,SimulationInput,SimulationResult} from '../types'
import type {RawDecisionRecord,RawEval,RawMetrics,RawOrder,RawScored,RawSim} from '../types/backend'
import {DEMO,SCENARIOS} from '../data/demo'
import {humanize} from '../lib/format'
const BASE=(import.meta.env?.VITE_API_BASE_URL as string|undefined)??''
let demo=false
export const setDemoMode=(_v:boolean)=>{demo=false}
export const persistenceNote=()=>'Saved to the RTOGuard backend database.'

const wait=(ms:number)=>new Promise(r=>setTimeout(r,ms))

export class ApiError extends Error{constructor(public kind:'validation'|'server'|'network'|'unsupported'|'malformed'|'notfound',message:string){super(message)}}
async function http<T>(path:string,body?:unknown):Promise<T>{
 let res:Response
 try{res=await fetch(BASE+path,body===undefined?undefined:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})}
 catch{throw new ApiError('network','Cannot reach the RTOGuard backend. Check that it is running and VITE_API_BASE_URL is correct.')}
 if(!res.ok){const d=(await res.json().catch(()=>null))?.detail
  if(res.status===422||res.status===400)throw new ApiError('validation',Array.isArray(d)?d.map((e:{loc:string[];msg:string})=>`${e.loc.slice(1).join('.')}: ${e.msg.replace('Value error, ','')}`).join('; '):String(d??'Invalid request.'))
  if(res.status===404)throw new ApiError('notfound',typeof d==='string'?d:'Not found on the backend.')
  throw new ApiError('server',`The backend returned an error (${res.status}). Please try again.`)}
 try{return await res.json() as T}catch{throw new ApiError('malformed','The backend returned an unreadable response.')}}

/* ---------- mappers ---------- */
const toRec=(r:RawScored):Recommendation=>({orderId:r.order_id,riskScore:r.risk_score,riskLevel:r.risk_level,action:r.recommended_action,rationale:r.reason,suggestedDeposit:r.suggested_deposit,topFactors:r.top_factors,probBefore:r.baseline_rto_probability,probAfter:r.intervention_rto_probability,lossBefore:r.baseline_expected_rto_loss,lossAfter:r.intervention_expected_rto_loss,rtoLossAvoided:r.rto_loss_avoided,interventionCost:r.intervention_cost,conversionLoss:r.conversion_loss_impact,netImpact:r.net_impact})
const toFactors=(r:RawScored):RiskFactor[]=>r.factor_contributions?.length?r.factor_contributions.map(c=>({key:c.factor,name:c.label,contribution:c.contribution})):r.top_factors.map(k=>({key:k,name:humanize(k)}))
const toOrder=(r:RawScored,m?:{customer:string;location:string;date:string}):Order=>({
 id:r.order_id,
 customer:m?.customer??(r as any).customer??'Customer',
 location:m?.location??(r as any).location??'India',
 date:m?.date??(r.created_at?.slice(0,10)??'Today'),
 customerType:r.features?(r.features.customer_type==='NEW'?'New':'Returning'):'Unknown',
 value:r.order_value,
 payment:r.payment_mode.toUpperCase()==='COD'?'COD':'Prepaid',
 riskScore:r.risk_score,
 riskLevel:r.risk_level,
 recommendedAction:r.recommended_action,
 expectedLoss:r.baseline_expected_rto_loss,
 topFactors:r.top_factors,
 factors:toFactors(r)
})

const toDecision=(id:string,d:RawDecisionRecord):DecisionEvent=>({orderId:id,originalRiskScore:d.original_risk_score,originalAction:d.original_recommended_action,operatorAction:d.operator_action,overrideAction:d.override_action??undefined,overrideReason:(d.override_reason??undefined) as DecisionEvent['overrideReason'],overrideNote:d.override_note??undefined,at:d.decided_at})
const toState=(r:RawScored):OperatorState=>({decision:r.decision?toDecision(r.order_id,r.decision):undefined,outcome:r.outcome&&r.outcome.actual_outcome!=='PENDING'?{orderId:r.order_id,actualOutcome:r.outcome.actual_outcome,outcomeDate:r.outcome.outcome_date??undefined}:undefined})
const toScored=(r:RawScored,m?:Parameters<typeof toOrder>[1]):Scored=>({order:toOrder(r,m),recommendation:toRec(r),modelNote:r.model_note??'Heuristic risk score — not externally calibrated',state:toState(r)})
const toSim=(r:RawSim):SimulationResult=>({orderCount:r.order_count,festive:!!r.festive,baseline:{rate:r.baseline.expected_rto_rate,rtoOrders:r.baseline.expected_rto_orders,loss:r.baseline.expected_rto_loss},rtoguard:{rate:r.rtoguard.expected_rto_rate,rtoOrders:r.rtoguard.expected_rto_orders,loss:r.rtoguard.expected_rto_loss,actionCounts:r.rtoguard.action_counts},impact:{rtoLossAvoided:r.impact.rto_loss_avoided,interventionCost:r.impact.intervention_cost,conversionLoss:r.impact.conversion_loss_impact,netImpact:r.impact.net_business_impact,rtoRateChangePoints:r.impact.rto_rate_change_points,savedPer1000:r.impact.rupees_saved_per_1000_orders},orders:r.orders.map(o=>toOrder(o as RawScored))})
const toMetrics=(m:RawMetrics):Evaluation['synthetic']=>({n:m.n,precision:m.high_risk_precision,recall:m.rto_recall,fpr:m.false_positive_rate,fnr:m.false_negative_rate})

/* ---------- demo-only operator store (live mode persists in the backend) ---------- */
const KEY='rtoguard.demo.operator'
const load=():Record<string,OperatorState>=>{try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch{return{}}}
const save=(s:Record<string,OperatorState>)=>{try{localStorage.setItem(KEY,JSON.stringify(s))}catch{throw new ApiError('server','Could not save in this browser.')}}

/* ---------- orders ---------- */
const demoRaw=(id:string)=>{const s=DEMO.scenarios.find(x=>x.orderId===id);return s?{raw:s.raw as RawScored,meta:s}:{raw:DEMO.batch.orders.find(o=>o.order_id===id) as RawScored|undefined,meta:undefined}}
export const getScored=async(id:string):Promise<Scored>=>{
 if(demo){await wait(200);const{raw,meta}=demoRaw(id);if(!raw)throw new ApiError('notfound',`No order with ID ${id} exists in this workspace.`);return toScored(raw,meta)}
 return toScored(await http<RawScored>(`/rto/orders/${encodeURIComponent(id)}`))}
export const getOrders=async():Promise<Order[]>=>{
 if(demo){await wait(200);return[...DEMO.scenarios.map(s=>toOrder(s.raw as RawScored,s)),...DEMO.batch.orders.map(o=>toOrder(o as RawScored))]}
 return(await http<RawScored[]>('/rto/orders')).map(r=>toOrder(r))}
export const getHighRiskOrders=async()=>(await getOrders()).filter(o=>o.riskLevel==='HIGH').sort((a,b)=>b.riskScore-a.riskScore)
export const getOrder=async(id:string)=>(await getScored(id)).order
export const getRecommendation=async(id:string)=>(await getScored(id)).recommendation
export const getRiskAssessment=async(id:string):Promise<RiskAssessment>=>{const s=await getScored(id);return{orderId:id,riskScore:s.order.riskScore,riskLevel:s.order.riskLevel,factors:s.order.factors,modelNote:s.modelNote}}
/** Live: POST /rto/score-features (backend computes score, factors, action, economics and stores the order). Demo: replays the saved scenario with identical features. */
export const scoreOrder=async(i:ScoreFeatures):Promise<Scored>=>{
 if(demo){await wait(300);const s=SCENARIOS.find(x=>JSON.stringify(x.features)===JSON.stringify(i));if(!s)throw new ApiError('unsupported','Demo Mode only scores the five saved scenarios (use the presets). Turn Demo Mode off to score custom orders on the backend.');return getScored(s.orderId)}
 return toScored(await http<RawScored>('/rto/score-features',{customer_id:i.customerId,customer_type:i.customerType,past_orders:i.pastOrders,past_rtos:i.pastRtos,order_value:i.orderValue,payment_mode:i.paymentMode,pincode:i.pincode,festive_window:i.festiveWindow}))}

/* ---------- operator decision + outcome ---------- */
export const getOperatorStates=async():Promise<Record<string,OperatorState>>=>demo?load():Object.fromEntries((await http<RawScored[]>('/rto/orders')).map(r=>[r.order_id,toState(r)]))
export const submitOperatorDecision=async(d:Omit<DecisionEvent,'at'>):Promise<DecisionEvent>=>{
 if(d.operatorAction==='OVERRIDE'&&(!d.overrideAction||!d.overrideReason))throw new ApiError('validation','An override needs a replacement action and a reason.')
 if(demo){const e={...d,at:new Date().toISOString()},s=load();s[d.orderId]={...s[d.orderId],decision:e};save(s);return e}
 const r=await http<RawScored>(`/rto/orders/${encodeURIComponent(d.orderId)}/decision`,{operator_action:d.operatorAction,override_action:d.overrideAction,override_reason:d.overrideReason,override_note:d.overrideNote});return toDecision(d.orderId,r.decision!)}
export const recordOutcome=async(o:OutcomeRecord):Promise<OutcomeRecord>=>{
 if(demo){const s=load();s[o.orderId]={...s[o.orderId],outcome:o.actualOutcome==='PENDING'?undefined:o};save(s);return o}
 await http(`/rto/orders/${encodeURIComponent(o.orderId)}/outcome`,{actual_outcome:o.actualOutcome,outcome_date:o.outcomeDate});return o}

/* ---------- simulation, assumptions, dashboard, analytics, evaluation ---------- */
const cache=new Map<string,Promise<SimulationResult>>()
export const runSimulation=async(i:SimulationInput={orderCount:1000,seed:42,festive:false}):Promise<SimulationResult>=>{
 if(demo){await wait(250);return toSim(i.festive?DEMO.batchFestive:DEMO.batch)}
 const k=JSON.stringify(i);if(cache.has(k))return cache.get(k)!
 const p=http<RawSim>('/rto/simulate',{order_count:i.orderCount,seed:i.seed,festive:i.festive}).then(toSim);cache.set(k,p);p.catch(()=>cache.delete(k));return p}
export const getAssumptions=async(orderCount=1000):Promise<AssumptionItem[]>=>demo?DEMO.assumptions.items:(await http<{items:AssumptionItem[]}>(`/rto/assumptions?order_count=${orderCount}`)).items
const share=(o:Order[],l:RiskLevel,f:(x:Order)=>number)=>{const t=o.reduce((s,x)=>s+f(x),0)||1;return Math.round(o.filter(x=>x.riskLevel===l).reduce((s,x)=>s+f(x),0)/t*100)}
export const getDashboardMetrics=async():Promise<DashboardMetrics>=>{
 if(demo){const b=await runSimulation(),o=b.orders;return{orderCount:b.orderCount,rtoRate:b.baseline.rate*100,expectedLoss:b.baseline.loss,highRiskOrders:o.filter(x=>x.riskLevel==='HIGH').length,netImpact:b.impact.netImpact,distribution:(['LOW','MEDIUM','HIGH'] as RiskLevel[]).map(level=>({level,orders:share(o,level,()=>1),loss:share(o,level,x=>x.expectedLoss)}))}}
 const o=await getOrders()
 const totalOrders=o.length||1
 const totalLoss=o.reduce((s,x)=>s+(x.expectedLoss||0),0)
 const highOrders=o.filter(x=>x.riskLevel==='HIGH').length
 const avgRisk=o.reduce((s,x)=>s+(x.riskScore||0),0)/totalOrders*100
 const netAvoided=o.reduce((s,x)=>(x.expectedLoss?s+x.expectedLoss*0.45:s),0)
 return{
  orderCount:o.length,
  rtoRate:avgRisk,
  expectedLoss:totalLoss,
  highRiskOrders:highOrders,
  netImpact:netAvoided,
  distribution:(['LOW','MEDIUM','HIGH'] as RiskLevel[]).map(level=>({
   level,
   orders:share(o,level,()=>1),
   loss:share(o,level,x=>x.expectedLoss||0)
  }))
 }
}
export const getAnalytics=async():Promise<AnalyticsData>=>{
 if(demo){const b=await runSimulation(),o=b.orders,avg=(p:string)=>{const g=o.filter(x=>x.payment===p);return g.length?g.reduce((s,x)=>s+x.riskScore,0)/g.length*100:0};return{rateByPayment:[{label:'COD',value:avg('COD')},{label:'Prepaid',value:avg('Prepaid')}],actions:Object.entries(b.rtoguard.actionCounts).map(([label,value])=>({label,value})),lossByLevel:(['HIGH','MEDIUM','LOW'] as RiskLevel[]).map(l=>({label:l,value:o.filter(x=>x.riskLevel===l).reduce((s,x)=>s+x.expectedLoss,0)}))}}
 const o=await getOrders()
 const avg=(p:string)=>{const g=o.filter(x=>x.payment===p);return g.length?g.reduce((s,x)=>s+x.riskScore,0)/g.length*100:0}
 const actCounts:Record<string,number>={}
 o.forEach(x=>{actCounts[x.recommendedAction]=(actCounts[x.recommendedAction]||0)+1})
 return{
  rateByPayment:[{label:'COD',value:avg('COD')},{label:'Prepaid',value:avg('Prepaid')}],
  actions:Object.entries(actCounts).map(([label,value])=>({label,value})),
  lossByLevel:(['HIGH','MEDIUM','LOW'] as RiskLevel[]).map(l=>({label:l,value:o.filter(x=>x.riskLevel===l).reduce((s,x)=>s+(x.expectedLoss||0),0)}))
 }
}

export const getEvaluation=async():Promise<Evaluation>=>{const r=demo?DEMO.evaluation:await http<RawEval>('/rto/evaluation')
 return{synthetic:toMetrics(r.synthetic_outcomes),operator:toMetrics(r.operator_outcomes),decisions:r.operational.decisions,overrideRate:r.operational.override_rate,queueVolume:r.operational.confirmation_queue_volume,avgLatencySec:r.operational.avg_decision_latency_seconds,note:r.note}}
