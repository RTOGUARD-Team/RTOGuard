import {createContext,ReactNode,useContext,useState} from 'react'
import {useNavigate} from 'react-router-dom'
import {SCENARIOS} from '../data/demo'
import {setDemoMode} from '../services/api'
interface Ctx{demo:boolean;setDemo:(v:boolean)=>void;orderId:string;setOrderId:(id:string)=>void}
const C=createContext<Ctx>(null!)
const DEFAULT=()=>'ord_101000'
/** Demo ON = saved synthetic sample, OFF = FastAPI. Order IDs differ per source, so switching returns to the dashboard. */
export const DemoProvider=({children}:{children:ReactNode})=>{const [orderId,setOrderId]=useState(DEFAULT())
 const setDemo=(_v:boolean)=>{setDemoMode(false)}
 return<C.Provider value={{demo:false,setDemo,orderId,setOrderId}}>{children}</C.Provider>}


export const useDemo=()=>useContext(C)
