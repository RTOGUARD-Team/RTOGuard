import {useSearchParams} from 'react-router-dom'
import {useAsync} from '../hooks/useAsync'
import {useDemo} from '../hooks/useDemo'
import {getOperatorStates,getOrders} from '../services/api'
import AsyncView from '../components/common/AsyncView'
import Disclosure from '../components/common/Disclosure'
import Panel,{PageTitle} from '../components/common/Panel'
import OrderTable from '../components/orders/OrderTable'
export default function Orders(){const{demo}=useDemo(),o=useAsync(getOrders,[demo]),st=useAsync(getOperatorStates,[demo]),[sp]=useSearchParams()
 return<><PageTitle title="Orders" sub="Every order scored before dispatch."/><Disclosure/><Panel title="All orders"><AsyncView state={o}>{l=><OrderTable key={sp.get('q')} orders={l} states={st.data} initialQuery={sp.get('q')??''} limit={1000}/>}</AsyncView></Panel></>}
