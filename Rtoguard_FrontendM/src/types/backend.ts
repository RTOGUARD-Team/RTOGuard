/** Raw response shapes of the FastAPI backend (snake_case). Mapped once, in services/api.ts. */
import type {Action,RiskLevel} from '.'
export interface RawEconomics{baseline_rto_probability:number;intervention_rto_probability:number;baseline_expected_rto_loss:number;intervention_expected_rto_loss:number;rto_loss_avoided:number;intervention_cost:number;conversion_loss_impact:number;net_impact:number}
export interface RawDecision extends RawEconomics{risk_score:number;risk_level:RiskLevel;recommended_action:Action;suggested_deposit:number;reason:string;top_factors:string[]}
export interface RawOrder extends RawDecision{order_id:string;order_value:number;payment_mode:string}
export interface RawFeatures{customer_type:'NEW'|'RETURNING';past_orders:number;past_rtos:number;pincode:string;festive_window:boolean}
export interface RawContribution{factor:string;label:string;contribution:number}
export interface RawDecisionRecord{operator_action:'ACCEPT'|'OVERRIDE';override_action?:Action|null;override_reason?:string|null;override_note?:string|null;decided_at:string;original_risk_score:number;original_recommended_action:Action}
export interface RawOutcome{actual_outcome:'DELIVERED'|'RTO'|'PENDING';outcome_date:string|null}
export interface RawScored extends RawOrder{features?:RawFeatures;factor_contributions?:RawContribution[];model_note?:string;created_at?:string;decision?:RawDecisionRecord|null;outcome?:RawOutcome|null}
export interface RawSim{order_count:number;festive?:boolean;baseline:{expected_rto_rate:number;expected_rto_orders:number;expected_rto_loss:number};rtoguard:{expected_rto_rate:number;expected_rto_orders:number;expected_rto_loss:number;action_counts:Record<string,number>};impact:{rto_loss_avoided:number;intervention_cost:number;conversion_loss_impact:number;net_business_impact:number;rto_rate_change_points:number;rupees_saved_per_1000_orders:number};orders:RawOrder[]}
export interface RawMetrics{n:number;high_risk_precision:number|null;rto_recall:number|null;false_positive_rate:number|null;false_negative_rate:number|null}
export interface RawEval{synthetic_outcomes:RawMetrics;operator_outcomes:RawMetrics;operational:{decisions:number;override_rate:number|null;confirmation_queue_volume:number;avg_decision_latency_seconds:number|null};note:string}
export interface RawAssumptions{synthetic:boolean;items:{label:string;value:string}[]}
export interface DemoData{scenarios:{scenarioId:string;label:string;orderId:string;customer:string;location:string;date:string;features:RawFeatures;raw:RawScored&{order_value:number}}[];batch:RawSim;batchFestive:RawSim;evaluation:RawEval;assumptions:RawAssumptions}
