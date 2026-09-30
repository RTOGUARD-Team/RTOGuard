import type {DemoData} from '../types/backend'
import type {Scenario} from '../types'
import raw from './fixtures.json'
/** Demo Mode data source: saved output of the real backend engines on synthetic data (see scripts/gen_fixtures.py). */
export const DEMO=raw as unknown as DemoData
export const SCENARIOS:Scenario[]=DEMO.scenarios.map(s=>({id:s.scenarioId,label:s.label,orderId:s.orderId,features:{customerType:s.features.customer_type,pastOrders:s.features.past_orders,pastRtos:s.features.past_rtos,orderValue:s.raw.order_value,paymentMode:s.raw.payment_mode as 'COD'|'PREPAID',pincode:s.features.pincode,festiveWindow:s.features.festive_window}}))
