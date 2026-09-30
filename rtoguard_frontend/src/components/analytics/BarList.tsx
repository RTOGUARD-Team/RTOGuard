import type {Labeled} from '../../types'
export default function BarList({rows,format,color='#6366F1'}:{rows:Labeled[];format:(n:number)=>string;color?:string}){const mx=Math.max(...rows.map(r=>r.value),1)
 return<div>{rows.map(r=><div key={r.label} className="my-2.5 grid grid-cols-[130px_1fr_56px] items-center gap-3"><span className="text-t2">{r.label}</span><div className="h-2 rounded bg-s3"><div className="h-full rounded transition-all duration-700" style={{width:r.value/mx*100+'%',background:color}}/></div><span className="tabular-nums">{format(r.value)}</span></div>)}</div>}
