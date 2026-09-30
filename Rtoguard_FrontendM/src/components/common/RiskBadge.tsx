import type {RiskLevel} from '../../types'
import {levelColor} from '../../lib/format'
export default function RiskBadge({level}:{level:RiskLevel}){const c=levelColor[level];return<span className="rounded-[5px] border px-2 py-px text-[11px] font-semibold" style={{color:c,background:c+'22',borderColor:c+'55'}}>{level}</span>}
