import {createContext,ReactNode,useContext,useState} from 'react'
import {useNavigate} from 'react-router-dom'
import {SCENARIOS} from '../data/demo'
import {setDemoMode} from '../services/api'
interface Ctx{demo:boolean;setDemo:(v:boolean)=>void;orderId:string;setOrderId:(id:string)=>void}
const C=createContext<Ctx>(null!)
const DEFAULT=()=>SCENARIOS.find(s=>s.id==='high')!.orderId
/** Demo ON = saved synthetic sample, OFF = FastAPI. Order IDs differ per source, so switching returns to the dashboard. */
export const DemoProvider=({children}:{children:ReactNode})=>{const nav=useNavigate(),[demo,set]=useState(true),[orderId,setOrderId]=useState(DEFAULT())
 const setDemo=(v:boolean)=>{setDemoMode(v);set(v);setOrderId(v?DEFAULT():'ORD-S0000');nav('/dashboard')}
 return<C.Provider value={{demo,setDemo,orderId,setOrderId}}>{children}</C.Provider>}
export const useDemo=()=>useContext(C)
