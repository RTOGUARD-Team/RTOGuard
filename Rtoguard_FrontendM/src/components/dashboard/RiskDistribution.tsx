import type {DashboardMetrics} from '../../types'
import {levelColor} from '../../lib/format'
type D=DashboardMetrics['distribution']
const Bar=({t,k,data}:{t:string;k:'orders'|'loss';data:D})=><div className="mt-4"><div className="mb-1 text-xs text-t3">{t}</div><div className="flex h-[22px] gap-0.5 overflow-hidden rounded">{data.map(d=><div key={d.level} className="pl-2 text-[11px] font-semibold leading-[22px] text-bg" style={{width:d[k]+'%',background:levelColor[d.level]}}>{d[k]}%</div>)}</div></div>
export default function RiskDistribution({data}:{data:D}){const hi=data.find(d=>d.level==='HIGH')!
 return<div><Bar t="Share of orders" k="orders" data={data}/><Bar t="Share of expected loss" k="loss" data={data}/><div className="mt-2 text-xs text-t3">Low · Medium · High</div><p className="mt-4 border-l-2 border-info pl-3 text-t2">High-risk orders are {hi.orders}% of volume but drive {hi.loss}% of expected RTO loss.</p></div>}
