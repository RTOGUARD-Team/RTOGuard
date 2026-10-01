import {NavLink,useLocation} from 'react-router-dom'
import {BarChart3,LayoutDashboard,Package,ShieldCheck,SlidersHorizontal,User} from 'lucide-react'
import {useDemo} from '../../hooks/useDemo'
export default function Sidebar(){const{demo,setDemo,orderId}=useDemo(),{pathname}=useLocation()
 const riskTo=`/orders/${orderId||'ord_101000'}`
 const NAV=[{to:'/dashboard',label:'Command Center',I:LayoutDashboard,on:pathname==='/dashboard'},{to:'/orders',label:'Orders',I:Package,on:pathname==='/orders'},{to:riskTo,label:'Risk Intelligence',I:ShieldCheck,on:pathname.startsWith('/orders/')},{to:`/simulator?order=${orderId}`,label:'Intervention Simulator',I:SlidersHorizontal,on:pathname==='/simulator'},{to:'/analytics',label:'Analytics',I:BarChart3,on:pathname==='/analytics'}]
 return<aside className="sticky top-0 flex h-screen w-[60px] flex-none flex-col gap-0.5 border-r border-line bg-s1 p-2.5 lg:w-[220px]">
 <div className="flex items-center gap-2 px-1.5 pb-4 pt-1 font-semibold"><span className="grid h-[22px] w-[22px] flex-none place-items-center rounded-md bg-brand"><ShieldCheck size={14}/></span><span className="hidden lg:inline">RTOGuard <span className="font-medium text-t3">AI</span></span></div>
 {NAV.map(n=><NavLink key={n.label} to={n.to} title={n.label} className={`flex items-center gap-2.5 rounded-md px-2.5 py-2 font-medium ${n.on?'bg-s3 text-t1 shadow-[inset_2px_0_0_#6366F1]':'text-t2 hover:bg-s2 hover:text-t1'}`}><n.I size={16}/><span className="hidden lg:inline">{n.label}</span></NavLink>)}
 <div className="flex-1"/>
 <div className="flex items-center gap-2.5 px-2.5 py-2 text-t2"><User size={16}/><span className="hidden lg:inline">Priya M.</span></div></aside>}
