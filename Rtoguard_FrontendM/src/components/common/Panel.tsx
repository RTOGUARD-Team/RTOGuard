import type {ReactNode} from 'react'
export const PageTitle=({title,sub}:{title:string;sub?:string})=><div className="mb-5"><h1 className="text-[22px] font-semibold tracking-tight">{title}</h1>{sub&&<p className="text-t2">{sub}</p>}</div>
export default function Panel({title,sub,className='',children}:{title?:string;sub?:string;className?:string;children:ReactNode}){
 return<section className={`rounded-lg border border-line bg-s1 p-[18px] ${className}`}>{title&&<div className="mb-3"><h2 className="font-semibold">{title}</h2>{sub&&<p className="text-xs text-t3">{sub}</p>}</div>}{children}</section>}
