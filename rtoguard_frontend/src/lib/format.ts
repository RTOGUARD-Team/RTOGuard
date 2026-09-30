import type {Action,OverrideReason,RiskLevel} from '../types'
export const inr=(n:number)=>'₹'+Math.round(n).toLocaleString('en-IN')
export const lakh=(n:number)=>Math.abs(n)>=1e5?'₹'+(n/1e5).toFixed(1)+'L':inr(n)
export const pct=(n:number)=>Math.round(n*100)+'%'
export const levelColor:Record<RiskLevel,string>={HIGH:'#EF4444',MEDIUM:'#F59E0B',LOW:'#22C55E'}
export const ACTION_LABEL:Record<Action,string>={SHIP_NORMAL:'Ship Normal',PARTIAL_DEPOSIT:'Partial Deposit',CONFIRMATION:'Confirmation',NO_COD_INTERVENTION:'No COD Intervention'}
export const ACTIONS=Object.keys(ACTION_LABEL) as Action[]
export const humanize=(k:string)=>k.replace(/_\d+$/,'').replace(/_/g,' ').replace(/^./,c=>c.toUpperCase())
export const CHART_TOOLTIP={contentStyle:{background:'#1A2130',border:'1px solid #252D3D',borderRadius:6,fontSize:12}}
export const REASON_LABEL:Record<OverrideReason,string>={VIP_CUSTOMER:'VIP customer',CUSTOMER_CONTACTED:'Customer contacted',REPEAT_BUSINESS:'Repeat business',MANUAL_VERIFICATION:'Manual verification',DATA_ISSUE:'Data issue',OTHER:'Other'}
export const REASONS=Object.keys(REASON_LABEL) as OverrideReason[]
export const dash=(n:number|null,f:(v:number)=>string)=>n===null?'—':f(n)
