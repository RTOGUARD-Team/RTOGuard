import {FormEvent, useState} from 'react'
import {Link} from 'react-router-dom'
import {useAsync} from '../hooks/useAsync'
import {useDemo} from '../hooks/useDemo'
import {getOperatorStates, persistenceNote, recordOutcome, scoreOrder, submitOperatorDecision} from '../services/api'
import {SCENARIOS} from '../data/demo'
import Panel, {PageTitle} from '../components/common/Panel'
import RiskScore from '../components/risk/RiskScore'
import RiskFactor from '../components/risk/RiskFactor'
import RecommendationCard from '../components/risk/RecommendationCard'
import DecisionPanel from '../components/risk/DecisionPanel'
import {ErrorState} from '../components/common/States'
import type {ScoreFeatures, Scored} from '../types'

interface ValidationErrors {
  customerType?: string
  pastOrders?: string
  pastRtos?: string
  orderValue?: string
  pincode?: string
}

const L = ({
  t,
  name,
  hint,
  errors,
  children,
}: {
  t: string
  name?: keyof ValidationErrors
  hint?: string
  errors?: ValidationErrors
  children: React.ReactNode
}) => (
  <div>
    <div className="mb-1 flex items-center justify-between">
      <label className="block text-xs font-medium text-t2">{t}</label>
      {hint && <span className="text-[11px] text-t3">{hint}</span>}
    </div>
    {children}
    {name && errors && errors[name] && (
      <p className="mt-1 text-xs font-medium text-hi animate-fade">{errors[name]}</p>
    )}
  </div>
)

export default function ScoreOrder() {
  const {demo} = useDemo()
  const [f, setF] = useState<any>(SCENARIOS[2].features)
  const [errors, setErrors] = useState<ValidationErrors>({})
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<Error>()
  const [res, setRes] = useState<Scored>()
  const op = useAsync(getOperatorStates, [demo])

  // Field validator
  const validateField = (name: string, value: any, allValues: any): string | undefined => {
    if (name === 'orderValue') {
      const val = Number(value)
      if (value === '' || value === undefined || value === null) return 'Order value is required'
      if (isNaN(val) || val <= 0) return 'Must be greater than ₹0'
      if (val > 1000000) return 'Cannot exceed ₹10,00,000'
    }
    if (name === 'pincode') {
      const pin = String(value || '').trim()
      if (!pin) return 'Pincode is required'
      if (!/^\d{6}$/.test(pin)) return 'Must be exactly 6 digits'
      if (pin.startsWith('0')) return 'Cannot start with 0'
    }
    if (allValues.customerType === 'RETURNING') {
      if (name === 'pastOrders') {
        const val = Number(value)
        if (value === '' || isNaN(val) || val < 1) return 'Returning customer must have ≥ 1 order'
      }
      if (name === 'pastRtos') {
        const rtos = Number(value)
        const orders = Number(allValues.pastOrders)
        if (value !== '' && !isNaN(rtos) && rtos < 0) return 'Cannot be negative'
        if (!isNaN(rtos) && !isNaN(orders) && rtos > orders) return 'Cannot exceed past orders'
      }
    }
    return undefined
  }

  // Full form validator
  const validateForm = (values: any): ValidationErrors => {
    const errs: ValidationErrors = {}
    const orderValErr = validateField('orderValue', values.orderValue, values)
    if (orderValErr) errs.orderValue = orderValErr

    const pinErr = validateField('pincode', values.pincode, values)
    if (pinErr) errs.pincode = pinErr

    if (values.customerType === 'RETURNING') {
      const pastOrdersErr = validateField('pastOrders', values.pastOrders, values)
      if (pastOrdersErr) errs.pastOrders = pastOrdersErr

      const pastRtosErr = validateField('pastRtos', values.pastRtos, values)
      if (pastRtosErr) errs.pastRtos = pastRtosErr
    }
    return errs
  }

  const set = (k: string, v: any) => {
    const next = {...f, [k]: v}
    setF(next)
    // Clear or update field-specific error as user types
    const fieldErr = validateField(k, v, next)
    setErrors(prev => {
      const updated = {...prev}
      if (fieldErr) updated[k as keyof ValidationErrors] = fieldErr
      else delete updated[k as keyof ValidationErrors]
      // Also re-validate dependent field (pastRtos depends on pastOrders)
      if (k === 'pastOrders' && next.customerType === 'RETURNING') {
        const rtoErr = validateField('pastRtos', next.pastRtos, next)
        if (rtoErr) updated.pastRtos = rtoErr
        else delete updated.pastRtos
      }
      return updated
    })
  }

  const handleCustomerTypeChange = (type: 'NEW' | 'RETURNING') => {
    if (type === 'NEW') {
      setF({...f, customerType: 'NEW', pastOrders: 0, pastRtos: 0})
      setErrors(prev => {
        const next = {...prev}
        delete next.pastOrders
        delete next.pastRtos
        return next
      })
    } else {
      const currOrders = Number(f.pastOrders)
      const newOrders = currOrders > 0 ? currOrders : 1
      setF({...f, customerType: 'RETURNING', pastOrders: newOrders})
      setErrors(prev => {
        const next = {...prev}
        delete next.pastOrders
        delete next.pastRtos
        return next
      })
    }
  }

  const handlePreset = (features: any) => {
    setF(features)
    setErrors({})
    setErr(undefined)
  }

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    const validationErrors = validateForm(f)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    setErrors({})
    setBusy(true)
    setErr(undefined)
    try {
      const payload: ScoreFeatures = {
        ...f,
        customerId: f.customerId ? String(f.customerId).trim() : undefined,
        customerType: f.customerType,
        pastOrders: f.customerType === 'NEW' ? 0 : Number(f.pastOrders) || 0,
        pastRtos: f.customerType === 'NEW' ? 0 : Number(f.pastRtos) || 0,
        orderValue: Number(f.orderValue) || 0,
        pincode: String(f.pincode).trim(),
      }
      const r = await scoreOrder(payload)
      setRes(r)
      op.retry()
    } catch (x) {
      setErr(x as Error)
      setRes(undefined)
    } finally {
      setBusy(false)
    }
  }



  const isNew = f.customerType === 'NEW'

  return (
    <>
      <PageTitle
        title="Score New Order"
        sub="Submit order and customer context. The backend computes the risk score, factors, action and economics."
      />
      <Panel className="mb-4">
        <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-t3">
          Presets:
          {SCENARIOS.map(s => (
            <button
              key={s.id}
              type="button"
              className="btn py-1 text-xs"
              onClick={() => handlePreset(s.features)}
            >
              {s.label}
            </button>
          ))}
        </div>
        <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <L t="Customer ID (Optional)" hint="e.g. 1, 101, CUS-1001 or new">
            <input
              className="field"
              type="text"
              placeholder="e.g. 1 or CUS-1001"
              value={f.customerId ?? ''}
              onChange={e => set('customerId', e.target.value.trim())}
            />
          </L>

          <L t="Customer type" errors={errors}>
            <select
              className="field"
              value={f.customerType}
              onChange={e => handleCustomerTypeChange(e.target.value as 'NEW' | 'RETURNING')}
            >
              <option value="NEW">New (First Order)</option>
              <option value="RETURNING">Returning (Repeat Customer)</option>
            </select>
          </L>

          <L t="Past orders" name="pastOrders" hint={isNew ? '0 for new customer' : undefined} errors={errors}>
            <input
              className={`field transition-colors ${
                errors.pastOrders ? 'border-hi focus:border-hi focus:ring-1 focus:ring-hi' : ''
              } ${isNew ? 'cursor-not-allowed opacity-50 bg-s1' : ''}`}
              type="text"
              inputMode="numeric"
              placeholder={isNew ? '0' : '1'}
              disabled={isNew}
              value={isNew ? 0 : f.pastOrders ?? ''}
              onChange={e => set('pastOrders', e.target.value.replace(/\D/g, ''))}
            />
          </L>

          <L t="Past RTOs" name="pastRtos" hint={isNew ? '0 for new customer' : undefined} errors={errors}>
            <input
              className={`field transition-colors ${
                errors.pastRtos ? 'border-hi focus:border-hi focus:ring-1 focus:ring-hi' : ''
              } ${isNew ? 'cursor-not-allowed opacity-50 bg-s1' : ''}`}
              type="text"
              inputMode="numeric"
              placeholder="0"
              disabled={isNew}
              value={isNew ? 0 : f.pastRtos ?? ''}
              onChange={e => set('pastRtos', e.target.value.replace(/\D/g, ''))}
            />
          </L>

          <L t="Order value (₹)" name="orderValue" errors={errors}>
            <input
              className={`field transition-colors ${
                errors.orderValue ? 'border-hi focus:border-hi focus:ring-1 focus:ring-hi' : ''
              }`}
              type="text"
              inputMode="numeric"
              placeholder="e.g. 1499"
              value={f.orderValue ?? ''}
              onChange={e => set('orderValue', e.target.value.replace(/\D/g, ''))}
            />
          </L>

          <L t="Payment mode" errors={errors}>
            <select
              className="field"
              value={f.paymentMode}
              onChange={e => set('paymentMode', e.target.value as 'COD' | 'PREPAID')}
            >
              <option value="COD">COD (Cash on Delivery)</option>
              <option value="PREPAID">Prepaid</option>
            </select>
          </L>

          <L t="Pincode (6 digits)" name="pincode" errors={errors}>
            <input
              className={`field transition-colors ${
                errors.pincode ? 'border-hi focus:border-hi focus:ring-1 focus:ring-hi' : ''
              }`}
              type="text"
              inputMode="numeric"
              maxLength={6}
              placeholder="e.g. 400001"
              value={f.pincode ?? ''}
              onChange={e => set('pincode', e.target.value.replace(/\D/g, '').slice(0, 6))}
            />
          </L>

          <label className="flex items-center gap-2 pb-2 text-t2 self-end cursor-pointer">
            <input
              type="checkbox"
              className="rounded border-line bg-s2 text-brand focus:ring-0"
              checked={!!f.festiveWindow}
              onChange={e => set('festiveWindow', e.target.checked)}
            />
            <span>Festive window</span>
          </label>

          <div className="flex items-end">
            <button className="btn btn-p w-full justify-center" disabled={busy}>
              {busy ? 'Scoring…' : 'Score Order'}
            </button>
          </div>
        </form>

        {demo && (
          <p className="mt-3 text-xs text-t3">
            Demo Mode replays the five saved scenarios. Turn it off to score any order on the backend.
          </p>
        )}
      </Panel>

      {err && <ErrorState title="Could not score this order" message={err.message} />}

      {res && (
        <>
          <p className="mb-3 text-t2">
            Saved as <b className="text-t1">{res.order.id}</b> in the decision queue.{' '}
            <Link className="text-brand underline" to="/dashboard">
              Open queue
            </Link>
          </p>
          <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
            <div className="space-y-4">
              <Panel>
                <RiskScore
                  score={res.order.riskScore}
                  level={res.order.riskLevel}
                  loss={res.order.expectedLoss}
                />
                <p className="mt-3 text-xs text-t3">{res.modelNote}</p>
              </Panel>
              <Panel title="Why is this order risky?">
                {res.order.factors.map(x => (
                  <RiskFactor key={x.key} f={x} />
                ))}
              </Panel>
            </div>
            <div className="space-y-4">
              <RecommendationCard r={res.recommendation} />
              <DecisionPanel
                key={res.order.id}
                orderId={res.order.id}
                riskScore={res.order.riskScore}
                action={res.recommendation.action}
                state={op.data?.[res.order.id]}
                note={persistenceNote()}
                onDecide={async d => {
                  await submitOperatorDecision(d)
                  op.retry()
                }}
                onOutcome={async x => {
                  await recordOutcome(x)
                  op.retry()
                }}
              />
            </div>
          </div>
        </>
      )}
    </>
  )
}
