import {useAsync} from '../hooks/useAsync'
import {useDemo} from '../hooks/useDemo'
import {getDashboardMetrics,getHighRiskOrders,getOperatorStates} from '../services/api'
import AsyncView from '../components/common/AsyncView'
import Disclosure from '../components/common/Disclosure'
import Panel,{PageTitle} from '../components/common/Panel'
import MetricCard from '../components/common/MetricCard'
import {EmptyState} from '../components/common/States'
import RiskDistribution from '../components/dashboard/RiskDistribution'
import OrderTable from '../components/orders/OrderTable'
import {lakh} from '../lib/format'
export default function Dashboard(){const{demo}=useDemo(),m=useAsync(getDashboardMetrics,[demo]),o=useAsync(getHighRiskOrders,[demo]),st=useAsync(getOperatorStates,[demo])
 return<><PageTitle title="RTO Risk Command Center" sub="Monitor high-risk orders and prevent avoidable losses before dispatch."/><Disclosure/>
 <AsyncView state={m}>{d=><><div className="mb-4 grid grid-cols-2 rounded-lg border border-line bg-s1 lg:grid-cols-[1.3fr_1fr_1fr_1fr]">
 <MetricCard large label="Expected RTO Rate" value={d.rtoRate.toFixed(1)+'%'} hint={`${d.orderCount.toLocaleString('en-IN')} orders, before intervention`}/>
 <MetricCard label="Expected RTO Loss" value={lakh(d.expectedLoss)} hint="Baseline, no intervention"/>
 <MetricCard label="High-Risk Orders" value={d.highRiskOrders.toLocaleString('en-IN')} hint="Risk score ≥ 0.60"/>
 <MetricCard label="Net Business Impact" value={lakh(d.netImpact)} hint="After intervention and conversion cost" tone="text-lo"/></div>
 <Panel className="mb-4" title="Risk distribution" sub="Share of orders vs share of expected loss"><RiskDistribution data={d.distribution}/></Panel></>}</AsyncView>
 <Panel title="Decision queue" sub="Highest-risk orders first"><AsyncView state={o}>{list=>list.length?<OrderTable orders={list} states={st.data} limit={25}/>:<EmptyState title="No high-risk orders" message="Nothing needs intervention right now."/>}</AsyncView></Panel></>}
