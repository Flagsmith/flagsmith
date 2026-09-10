import { getStore } from 'common/store'
import { projectFlagService } from 'common/services/useProjectFlag'
import { createMultivariateOption } from 'common/services/useMultivariateOption'
import { Req } from 'common/types/requests'
import { ProjectFlag } from 'common/types/responses'
import Utils from 'common/utils/utils'

type Store = ReturnType<typeof getStore>

export const ONBOARDING_FLAG_CONTROL_VALUE = 'control'
export const ONBOARDING_FLAG_VARIATIONS = ['variant']

export type CreateOnboardingFlagInput = {
  projectId: number
  name: string
  description?: string | null
  tags?: number[]
}

// The onboarding flag is multivariate (control + one 0% variation) so a
// fresh user can start an experiment on it straight away.
export async function createOnboardingFlag(
  store: Store,
  { description, name, projectId, tags }: CreateOnboardingFlagInput,
): Promise<ProjectFlag> {
  const flag = await store
    .dispatch(
      projectFlagService.endpoints.createProjectFlag.initiate({
        body: {
          description,
          initial_value: ONBOARDING_FLAG_CONTROL_VALUE,
          name,
          project: projectId,
          tags,
          type: 'MULTIVARIATE',
        } as Req['createProjectFlag']['body'],
        project_id: projectId,
      }),
    )
    .unwrap()
  // Sequential so options get ascending ids in input order.
  for (const value of ONBOARDING_FLAG_VARIATIONS) {
    await createMultivariateOption(store, {
      body: {
        ...Utils.valueToFeatureState(value),
        default_percentage_allocation: 0,
        feature: flag.id,
        key: value,
      },
      feature_id: flag.id,
      project_id: projectId,
    })
  }
  return flag
}
