// These stores pull in `window` globals (via the flux dispatcher) that
// aren't available under the jest `node` test environment, so they're
// mocked out to allow `common/utils/utils` to load for real.
jest.mock('common/stores/account-store', () => ({}))
jest.mock('common/stores/project-store', () => ({}))
jest.mock('common/store', () => ({
  getStore: () => ({ getState: () => ({}) }),
}))
jest.mock('@flagsmith/flagsmith', () => ({
  getValue: (_key: string, opts: { fallback: unknown }) => opts.fallback,
}))

import Utils from 'common/utils/utils'
import { SegmentCondition } from 'common/types/responses'

const buildRule = (overrides: Partial<SegmentCondition>): SegmentCondition => ({
  operator: 'EQUAL',
  property: 'trait',
  value: '',
  ...overrides,
})

describe('validateRule', () => {
  it('returns false for a falsy rule', () => {
    expect(Utils.validateRule(undefined as unknown as SegmentCondition)).toBe(
      false,
    )
  })

  it('returns true for a rule marked as deleted regardless of its value', () => {
    const rule = buildRule({
      delete: true,
      operator: 'MODULO',
      value: undefined as unknown as string,
    })
    expect(() => Utils.validateRule(rule)).not.toThrow()
    expect(Utils.validateRule(rule)).toBe(true)
  })

  describe('does not throw and returns false when value is missing', () => {
    it.each<[string, SegmentCondition['value']]>([
      ['undefined', undefined as unknown as string],
      ['null', null],
      ['empty string', ''],
    ])('MODULO with %s value', (_label, value) => {
      const rule = buildRule({ operator: 'MODULO', value })
      expect(() => Utils.validateRule(rule)).not.toThrow()
      expect(Utils.validateRule(rule)).toBe(false)
    })

    it.each<[string, SegmentCondition['value']]>([
      ['undefined', undefined as unknown as string],
      ['null', null],
      ['empty string', ''],
    ])('semver operator with %s value', (_label, value) => {
      const rule = buildRule({ operator: 'GREATER_THAN:semver', value })
      expect(() => Utils.validateRule(rule)).not.toThrow()
      expect(Utils.validateRule(rule)).toBe(false)
    })
  })

  it('does not throw when value is a non-string type for MODULO', () => {
    const rule = buildRule({ operator: 'MODULO', value: true })
    expect(() => Utils.validateRule(rule)).not.toThrow()
    expect(Utils.validateRule(rule)).toBe(false)
  })

  it('does not throw when value is a non-string type for a semver operator', () => {
    const rule = buildRule({ operator: 'GREATER_THAN:semver', value: true })
    expect(() => Utils.validateRule(rule)).not.toThrow()
    expect(Utils.validateRule(rule)).toBe(false)
  })

  it('is valid for a hideValue operator (e.g. IS_SET) even with a null value', () => {
    const rule = buildRule({ operator: 'IS_SET', value: null })
    expect(() => Utils.validateRule(rule)).not.toThrow()
    expect(Utils.validateRule(rule)).toBe(true)
  })

  it('validates a correct MODULO value', () => {
    const rule = buildRule({ operator: 'MODULO', value: '2|1' })
    expect(Utils.validateRule(rule)).toBe(true)
  })

  it('validates a correct semver value', () => {
    const rule = buildRule({
      operator: 'GREATER_THAN:semver',
      value: '1.0.0:semver',
    })
    expect(Utils.validateRule(rule)).toBe(true)
  })

  it('rejects an invalid semver value', () => {
    const rule = buildRule({
      operator: 'GREATER_THAN:semver',
      value: 'not-a-version',
    })
    expect(Utils.validateRule(rule)).toBe(false)
  })
})

describe('getPlanPermission', () => {
  beforeEach(() => {
    jest.spyOn(Utils, 'isEnterpriseImage').mockReturnValue(false)
    jest.spyOn(Utils, 'isSaas').mockReturnValue(true)
  })
  afterEach(() => jest.restoreAllMocks())

  it.each([
    ['scale-up', 'AUDIT', true],
    ['enterprise', 'AUDIT', true],
    ['start-up', 'AUDIT', false],
    ['free', 'AUDIT', false],
    ['enterprise', 'SCIM', true],
    ['scale-up', 'SCIM', false],
  ] as const)(
    'hardcoded features: plan=%s feature=%s => %s',
    (plan, feature, expected) => {
      expect(Utils.getPlanPermission(plan, feature)).toBe(expected)
    },
  )

  describe('WAREHOUSE with legacy array value', () => {
    it('allows free plan when value includes "free"', () => {
      jest.spyOn(Utils, 'getFlagsmithJSONValue').mockReturnValue(['free'])
      expect(Utils.getPlanPermission('free', 'WAREHOUSE')).toBe(true)
    })

    it('blocks free plan when value is empty', () => {
      jest.spyOn(Utils, 'getFlagsmithJSONValue').mockReturnValue([])
      expect(Utils.getPlanPermission('free', 'WAREHOUSE')).toBe(false)
    })

    it('allows scale-up when value includes "scale-up"', () => {
      jest.spyOn(Utils, 'getFlagsmithJSONValue').mockReturnValue(['scale-up'])
      expect(Utils.getPlanPermission('scale-up', 'WAREHOUSE')).toBe(true)
    })
  })

  describe('WAREHOUSE with object value', () => {
    it('allows free plan when allowed_plans includes "free"', () => {
      jest.spyOn(Utils, 'getFlagsmithJSONValue').mockReturnValue({
        allowed_plans: ['free'],
        auto_connect_warehouse: true,
      })
      expect(Utils.getPlanPermission('free', 'WAREHOUSE')).toBe(true)
    })

    it('blocks free plan when allowed_plans does not include "free"', () => {
      jest
        .spyOn(Utils, 'getFlagsmithJSONValue')
        .mockReturnValue({ allowed_plans: ['scale-up'] })
      expect(Utils.getPlanPermission('free', 'WAREHOUSE')).toBe(false)
    })

    it('falls back to enterprise with malformed value', () => {
      jest
        .spyOn(Utils, 'getFlagsmithJSONValue')
        .mockReturnValue({ allowed_plans: 'not-an-array' })
      expect(Utils.getPlanPermission('enterprise', 'WAREHOUSE')).toBe(true)
      expect(Utils.getPlanPermission('scale-up', 'WAREHOUSE')).toBe(false)
    })
  })
})
