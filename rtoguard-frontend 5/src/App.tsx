import {Navigate,Route,Routes} from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import Dashboard from './pages/Dashboard'
import Orders from './pages/Orders'
import OrderDetail from './pages/OrderDetail'
import Simulator from './pages/Simulator'
import ScoreOrder from './pages/ScoreOrder'
import Analytics from './pages/Analytics'
import {ErrorState} from './components/common/States'
export default function App(){return(<Routes><Route element={<AppShell/>}>
<Route index element={<Navigate to="/dashboard" replace/>}/><Route path="/dashboard" element={<Dashboard/>}/><Route path="/orders" element={<Orders/>}/><Route path="/orders/:orderId" element={<OrderDetail/>}/><Route path="/simulator" element={<Simulator/>}/><Route path="/score" element={<ScoreOrder/>}/><Route path="/analytics" element={<Analytics/>}/>
<Route path="*" element={<ErrorState title="Page not found" message="This route does not exist."/>}/></Route></Routes>)}
