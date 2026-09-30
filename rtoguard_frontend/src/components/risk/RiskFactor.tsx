import type {RiskFactor as F} from '../../types'
export default function RiskFactor({f}:{f:F}){const c=f.contribution
 return<div className="border-b border-line py-2.5 last:border-0"><div className="flex justify-between"><b>{f.name}</b>{c!==undefined&&<span className={`tabular-nums ${c>0?'text-t1':'text-lo'}`}>{c>0?'+':''}{Math.round(c*100)}%</span>}</div>
 {c!==undefined&&<div className="mt-1.5 h-1.5 rounded bg-s3"><div className={`h-full rounded transition-all duration-1000 ${c>0?'bg-hi':'bg-lo'}`} style={{width:Math.min(100,Math.abs(c)/0.3*100)+'%'}}/></div>}</div>}
