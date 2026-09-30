import {useState,type FormEvent} from 'react'
import {Link,useLocation,useNavigate} from 'react-router-dom'
import {Search} from 'lucide-react'
import DemoModeSelector from '../common/DemoModeSelector'
import {useDemo} from '../../hooks/useDemo'
const TITLES:[string,string][]=[['/dashboard','Command Center'],['/score','Score New Order'],['/orders/','Risk Intelligence'],['/orders','Orders'],['/simulator','Intervention Simulator'],['/analytics','Analytics']]
export default function Header(){const{pathname}=useLocation(),nav=useNavigate(),{demo,setDemo}=useDemo(),[q,setQ]=useState('')
 const title=TITLES.find(t=>pathname.startsWith(t[0]))?.[1]??'Not found'
 const go=(e:FormEvent)=>{e.preventDefault();nav('/orders?q='+encodeURIComponent(q))}
 return<header className="sticky top-0 z-10 flex h-14 items-center gap-3 border-b border-line bg-bg px-6"><div className="text-t2">RTOGuard <span className="text-t3">/</span> <b className="font-semibold text-t1">{title}</b></div><div className="flex-1"/>
 {demo&&<DemoModeSelector/>}<Link to="/score" className="btn btn-p py-1.5">Score New Order</Link><form onSubmit={go} className="relative"><Search size={14} className="absolute left-2.5 top-2.5 text-t3"/><input className="field w-48 pl-8" placeholder="Search orders" aria-label="Search orders" value={q} onChange={e=>setQ(e.target.value)}/></form>
 <button role="switch" aria-checked={demo} aria-label="Demo mode" onClick={()=>setDemo(!demo)} className={`relative h-5 w-[34px] rounded-full ${demo?'bg-brand':'bg-line'}`}><span className={`absolute top-[3px] h-3.5 w-3.5 rounded-full bg-white transition-all ${demo?'left-[17px]':'left-[3px]'}`}/></button><span className="text-xs text-t3">Demo</span>
 <span className="flex items-center gap-2 text-xs text-t2"><span className="h-[7px] w-[7px] rounded-full bg-lo shadow-[0_0_0_3px_#22c55e22]"/>System Operational</span></header>}
