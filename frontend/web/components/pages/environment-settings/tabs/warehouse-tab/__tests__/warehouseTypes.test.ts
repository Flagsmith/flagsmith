import {
  getConfigurableWarehouseTypes,
  getMinimumPlans,
  getPlanAvailabilityMessage,
  getWarehouseMinimumPlan,
  getWarehouseTypeStatus,
  MinimumPlans,
  WarehouseTypeOption,
  WarehouseTypeStatus,
} from 'components/pages/environment-settings/tabs/warehouse-tab/warehouseTypes'
import { PlanFamily } from 'common/utils/plans'

const minimumPlans: MinimumPlans = {
  clickhouse: 'scale-up',
  databricks: 'enterprise',
  flagsmith: null,
  snowflake: 'scale-up',
}
const flagValue = JSON.stringify({
  auto_connect_flagsmith: true,
  minimum_plans: minimumPlans,
})

describe('getConfigurableWarehouseTypes', () => {
  it.each([
    [false, ['clickhouse', 'databricks']],
    [true, ['flagsmith', 'clickhouse', 'databricks']],
  ])('isSaas=%s => %j', (isSaas, expected) => {
    expect(getConfigurableWarehouseTypes(isSaas)).toEqual(expected)
  })
})

describe('getMinimumPlans', () => {
  it.each<[boolean, unknown, MinimumPlans]>([
    [true, flagValue, minimumPlans],
    [false, flagValue, {}],
    [true, JSON.stringify({ minimum_plans: ['scale-up'] }), {}],
    [true, JSON.stringify(['scale-up']), {}],
    [true, 'not json', {}],
    [true, null, {}],
  ])('enabled=%s value=%s => %j', (enabled, value, expected) => {
    expect(getMinimumPlans({ enabled, value })).toEqual(expected)
  })
})

describe('getWarehouseMinimumPlan', () => {
  it.each<[WarehouseTypeOption, MinimumPlans, PlanFamily]>([
    ['clickhouse', minimumPlans, 'scale-up'],
    ['databricks', minimumPlans, 'enterprise'],
    ['flagsmith', minimumPlans, 'free'],
    ['bigquery', minimumPlans, 'free'],
    ['clickhouse', { clickhouse: 'free' }, 'free'],
    ['clickhouse', { clickhouse: 'gold' }, 'free'],
    ['clickhouse', { clickhouse: ['scale-up'] }, 'free'],
    ['clickhouse', {}, 'free'],
  ])('%s with %j => %s', (type, plans, expected) => {
    expect(getWarehouseMinimumPlan(type, plans)).toBe(expected)
  })
})

describe('getWarehouseTypeStatus', () => {
  it.each<[WarehouseTypeOption, string | null, boolean, WarehouseTypeStatus]>([
    ['flagsmith', 'free', true, 'available'],
    ['clickhouse', 'free', true, 'plan-gated'],
    ['clickhouse', 'startup', true, 'plan-gated'],
    ['clickhouse', 'scale-up', true, 'available'],
    ['clickhouse', 'enterprise', true, 'available'],
    ['databricks', 'scale-up', true, 'plan-gated'],
    ['databricks', 'enterprise', true, 'available'],
    ['snowflake', 'enterprise', true, 'coming-soon'],
    ['bigquery', 'enterprise', true, 'coming-soon'],
    ['clickhouse', 'free', false, 'available'],
    ['databricks', null, false, 'available'],
    ['flagsmith', 'enterprise', false, 'coming-soon'],
  ])('%s on %s (isSaas=%s) => %s', (type, planId, isSaas, expected) => {
    expect(getWarehouseTypeStatus(type, { isSaas, minimumPlans, planId })).toBe(
      expected,
    )
  })
})

describe('getPlanAvailabilityMessage', () => {
  it.each<[PlanFamily, string]>([
    ['start-up', 'Available on Startup, Scale-Up and Enterprise plans'],
    ['scale-up', 'Available on Scale-Up and Enterprise plans'],
    ['enterprise', 'Available on the Enterprise plan'],
  ])('%s => %s', (minimum, expected) => {
    expect(getPlanAvailabilityMessage(minimum)).toBe(expected)
  })
})
