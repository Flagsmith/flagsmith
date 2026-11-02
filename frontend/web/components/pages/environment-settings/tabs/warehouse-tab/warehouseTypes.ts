import { WarehouseType } from 'common/types/responses'
import {
  getPlanFamily,
  isPlanAtLeast,
  PLAN_FAMILIES,
  planFamilyNames,
  PlanFamily,
} from 'common/utils/plans'

export type WarehouseTypeOption = WarehouseType | 'bigquery'

export const WAREHOUSES_FLAG = 'experimentation_warehouses'

// The managed Flagsmith warehouse only exists on SaaS.
export const getConfigurableWarehouseTypes = (
  isSaas: boolean,
): WarehouseTypeOption[] => [
  ...(isSaas ? (['flagsmith'] as const) : []),
  'clickhouse',
  'databricks',
]

export type MinimumPlans = Record<string, unknown>

const asObject = (value: unknown): Record<string, unknown> | undefined =>
  value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined

export const getMinimumPlans = (flag: {
  enabled: boolean
  value: unknown
}): MinimumPlans => {
  if (!flag.enabled || typeof flag.value !== 'string') return {}
  try {
    return asObject(asObject(JSON.parse(flag.value))?.minimum_plans) ?? {}
  } catch {
    return {}
  }
}

export const getWarehouseMinimumPlan = (
  type: WarehouseTypeOption,
  minimumPlans: MinimumPlans,
): PlanFamily => {
  const minimum = minimumPlans[type]
  return getPlanFamily(typeof minimum === 'string' ? minimum : '')
}

export type WarehouseGate = {
  isSaas: boolean
  minimumPlans: MinimumPlans
  planId: string | null | undefined
}

export type WarehouseTypeStatus = 'available' | 'plan-gated' | 'coming-soon'

const isWarehouseTypeAvailable = (
  type: WarehouseTypeOption,
  { isSaas, minimumPlans, planId }: WarehouseGate,
): boolean =>
  !isSaas || isPlanAtLeast(planId, getWarehouseMinimumPlan(type, minimumPlans))

export const getWarehouseTypeStatus = (
  type: WarehouseTypeOption,
  gate: WarehouseGate,
): WarehouseTypeStatus => {
  if (!getConfigurableWarehouseTypes(gate.isSaas).includes(type)) {
    return 'coming-soon'
  }
  return isWarehouseTypeAvailable(type, gate) ? 'available' : 'plan-gated'
}

export const getPlanAvailabilityMessage = (minimum: PlanFamily): string => {
  const names = PLAN_FAMILIES.slice(PLAN_FAMILIES.indexOf(minimum)).map(
    (family) => planFamilyNames[family],
  )
  if (names.length === 1) return `Available on the ${names[0]} plan`
  return `Available on ${names.slice(0, -1).join(', ')} and ${
    names[names.length - 1]
  } plans`
}
