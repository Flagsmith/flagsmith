import { BillingPeriod } from 'common/types/requests'
import { allowanceWindow, UsageBasis } from './utils'

// The note sits under the meter, so it can only compare over the window the
// meter shows. On any other period "that usage" would name a figure that is
// not on screen.
export const showsContribution = (
  basis: UsageBasis,
  period: BillingPeriod,
  projectId: number | undefined,
): boolean => !!projectId && period === allowanceWindow(basis)

export const contributionNote = (
  projectName: string,
  scopedTotal: number,
  organisationTotal: number,
): string | undefined =>
  organisationTotal > 0
    ? `${projectName} accounts for ${Math.round(
        (scopedTotal / organisationTotal) * 100,
      )}% of that usage.`
    : undefined
