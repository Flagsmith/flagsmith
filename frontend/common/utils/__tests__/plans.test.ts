import { getPlanFamily, isPlanAtLeast, PlanFamily } from 'common/utils/plans'

describe('getPlanFamily', () => {
  it.each<[string | null | undefined, PlanFamily]>([
    ['scale-up-v2', 'scale-up'],
    ['ScaleUp', 'scale-up'],
    ['startup-annual', 'start-up'],
    ['start-up', 'start-up'],
    ['enterprise-semiannual', 'enterprise'],
    ['free', 'free'],
    ['legacy-scale-up', 'free'],
    [null, 'free'],
  ])('%s => %s', (planId, expected) => {
    expect(getPlanFamily(planId)).toBe(expected)
  })
})

describe('isPlanAtLeast', () => {
  it.each<[string | null, PlanFamily, boolean]>([
    ['free', 'free', true],
    [null, 'start-up', false],
    ['startup', 'scale-up', false],
    ['scale-up', 'scale-up', true],
    ['enterprise', 'scale-up', true],
    ['scale-up', 'enterprise', false],
  ])('%s at least %s => %s', (planId, minimum, expected) => {
    expect(isPlanAtLeast(planId, minimum)).toBe(expected)
  })
})
