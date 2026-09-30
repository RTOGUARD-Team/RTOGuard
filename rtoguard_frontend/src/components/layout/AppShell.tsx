import {Outlet,useLocation} from 'react-router-dom'
import Sidebar from './Sidebar'
import {useDemo} from '../../hooks/useDemo'
import Header from './Header'
export default function AppShell(){const{pathname}=useLocation(),{demo}=useDemo()
 return<div className="flex min-h-screen"><Sidebar/><div className="min-w-0 flex-1"><Header/><main key={pathname+demo} className="mx-auto max-w-[1360px] animate-fade p-6"><Outlet/></main></div></div>}
