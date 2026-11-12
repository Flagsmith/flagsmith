export type Plan = 'free' | 'start-up' | 'scale-up' | 'enterprise' | null
export type PlanFamily = NonNullable<Plan>

export const planNames = {
  enterprise: 'Enterprise',
  free: 'Free',
  scaleUp: 'Scale-Up',
  startup: 'Startup',
}

export const PLAN_FAMILIES: PlanFamily[] = [
  'free',
  'start-up',
  'scale-up',
  'enterprise',
]

export const planFamilyNames: Record<PlanFamily, string> = {
  'enterprise': planNames.enterprise,
  'free': planNames.free,
  'scale-up': planNames.scaleUp,
  'start-up': planNames.startup,
}

export const getPlanFamily = (
  planId: string | null | undefined,
): PlanFamily => {
  const plan = (planId ?? '').replace(/-/g, '').toLowerCase()
  if (plan.startsWith('scaleup')) return 'scale-up'
  if (plan.startsWith('startup')) return 'start-up'
  if (plan.startsWith('enterprise')) return 'enterprise'
  return 'free'
}

export const isPlanAtLeast = (
  planId: string | null | undefined,
  minimum: PlanFamily,
): boolean =>
  PLAN_FAMILIES.indexOf(getPlanFamily(planId)) >= PLAN_FAMILIES.indexOf(minimum)
