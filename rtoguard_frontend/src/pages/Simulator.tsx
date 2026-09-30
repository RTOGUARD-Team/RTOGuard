import {useState} from 'react'
import {useAsync} from '../hooks/useAsync'
import {useDemo} from '../hooks/useDemo'
import {getAssumptions,runSimulation} from '../services/api'
import AsyncView from '../components/common/AsyncView'
import Disclosure from '../components/common/Disclosure'
import {PageTitle} from '../components/common/Panel'
import BatchSimulationView from '../components/simulator/BatchSimulationView'
export default function Simulator(){const{demo}=useDemo(),[n,setN]=useState(1000),[seed,setSeed]=useState(42),[fest,setFest]=useState(false),[k,setK]=useState({orderCount:1000,seed:42})
 const r=useAsync(()=>runSimulation({...k,festive:fest}),[k,fest,demo]),a=useAsync(()=>getAssumptions(k.orderCount),[k,demo])
 return<><PageTitle title="What happens if we intervene?" sub="Backend simulation: RTOGuard's recommended action applied to every order, with costs and conversion loss."/><Disclosure/>
 <div className="mb-4 flex flex-wrap items-end gap-3"><div><label className="mb-1 block text-xs text-t2">Orders</label><input className="field w-32" type="number" min={1} max={100000} disabled={demo} value={demo?100:n} onChange={e=>setN(+e.target.value||1)}/></div><div><label className="mb-1 block text-xs text-t2">Seed</label><input className="field w-28" type="number" disabled={demo} value={seed} onChange={e=>setSeed(+e.target.value||0)}/></div>
 <button className="btn btn-p" disabled={r.loading||demo} onClick={()=>setK({orderCount:n,seed})}>{r.loading?'Running simulation…':'Run Simulation'}</button>
 <label className="ml-auto flex cursor-pointer items-center gap-2 text-t2"><input type="checkbox" checked={fest} onChange={e=>setFest(e.target.checked)}/>Festive Mode <span className="text-xs text-t3">(configured assumption)</span></label></div>
 {demo&&<p className="mb-4 text-xs text-t3">Demo Mode replays a saved 100-order sample. Turn it off to run the 1,000-order simulation on the backend.</p>}
 <div className={r.loading?'opacity-60 transition-opacity':''}><AsyncView state={r}>{d=><BatchSimulationView r={d} assumptions={a.data??[]}/>}</AsyncView></div></>}
