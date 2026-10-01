import { PlanLimit } from 'components/shared/UsageBar/utils'
import { joinSentences } from './usageText'
import { allowanceWindowLabel, UsageBasis } from './utils'

export type PlanHeading = { title: string; hint: string }

export const planHeading = (
  basis: UsageBasis,
  limit: PlanLimit,
): PlanHeading => {
  const window = allowanceWindowLabel(basis)

  if (!limit) {
    return {
      hint: joinSentences(
        `API calls over ${window}.`,
        'This installation has no plan limit.',
      ),
      title: 'Your usage',
    }
  }

  return {
    hint: joinSentences(
      `Usage against your plan limit over ${window}.`,
      basis.window === 'rolling' &&
        basis.reason === 'no-period' &&
        'We are unable to show exact billing periods for your subscription plan.',
    ),
    title: 'Your plan',
  }
}
