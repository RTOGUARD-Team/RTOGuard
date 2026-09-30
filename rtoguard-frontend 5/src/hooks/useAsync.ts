import {useEffect,useState} from 'react'
export interface AsyncState<T>{data?:T;error?:Error;loading:boolean;retry:()=>void}
export function useAsync<T>(fn:()=>Promise<T>,deps:unknown[]=[]):AsyncState<T>{
 const [s,set]=useState<{data?:T;error?:Error;loading:boolean}>({loading:true}),[n,setN]=useState(0)
 useEffect(()=>{let live=true;set(x=>({...x,loading:true,error:undefined}))
  fn().then(d=>live&&set({data:d,loading:false}),e=>live&&set({error:e as Error,loading:false}))
  return()=>{live=false}},[...deps,n]) // eslint-disable-line react-hooks/exhaustive-deps
 return{...s,retry:()=>setN(v=>v+1)}}
