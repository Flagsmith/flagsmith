import { getStore } from 'common/store'
import {
  projectFlagService,
  removeProjectFlag,
} from 'common/services/useProjectFlag'
import { createMultivariateOption } from 'common/services/useMultivariateOption'
import { Req } from 'common/types/requests'
import { ProjectFlag } from 'common/types/responses'

type Store = ReturnType<typeof getStore>

export const ONBOARDING_FLAG_CONTROL_VALUE = 'control'
export const ONBOARDING_FLAG_VARIATION = 'variant'

export type CreateOnboardingFlagInput = {
  projectId: number
  name: string
  description?: ProjectFlag['description']
  tags?: ProjectFlag['tags']
}

export async function ensureOnboardingVariation(
  store: Store,
  flag: ProjectFlag,
): Promise<void> {
  if (flag.multivariate_options?.length) {
    return
  }
  const res = await createMultivariateOption(store, {
    body: {
      default_percentage_allocation: 0,
      feature: flag.id,
      key: ONBOARDING_FLAG_VARIATION,
      string_value: ONBOARDING_FLAG_VARIATION,
      type: 'unicode',
    },
    feature_id: flag.id,
    project_id: flag.project,
  })
  if (res.error) {
    throw res.error
  }
}

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
  try {
    await ensureOnboardingVariation(store, flag)
  } catch (error) {
    await removeProjectFlag(store, { flag_id: flag.id, project_id: projectId })
    throw error
  }
  return flag
}
