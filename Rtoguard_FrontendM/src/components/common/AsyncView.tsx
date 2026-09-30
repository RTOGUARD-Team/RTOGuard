import type {ReactNode} from 'react'
import type {AsyncState} from '../../hooks/useAsync'
import {ErrorState,LoadingState} from './States'
export default function AsyncView<T>({state,children}:{state:AsyncState<T>;children:(d:T)=>ReactNode}){
 if(state.error)return<ErrorState message={state.error.message} onRetry={state.retry}/>
 if(state.data===undefined)return<LoadingState/>
 return<>{children(state.data)}</>}
