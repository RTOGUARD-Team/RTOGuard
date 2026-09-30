import {useDemo} from '../../hooks/useDemo'
export default function Disclosure(){const{demo}=useDemo()
 return<div className="mb-4 rounded-md border border-info/30 bg-info/5 px-3 py-2 text-xs text-t2"><b className="text-info">Synthetic data.</b> {demo?'Demo Mode shows a saved sample of 100 synthetic orders scored by the RTOGuard engines. No real customer data.':'Live mode: dashboard and simulation use the backend\'s synthetic generator (1,000 orders, seed 42). The decision queue holds seeded synthetic orders plus any order you score. Nothing here is observed data.'}</div>}
