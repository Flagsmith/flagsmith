import { FC, useEffect, useState } from 'react'
import { useGetEnvironmentsQuery } from './useEnvironment'
import { Environment, FeatureState, Res } from 'common/types/responses'
import { getFeatureStates } from './useFeatureState'
import { getStore } from 'common/store'
import keyBy from 'lodash/keyBy'

type useAllFeatureStatesType = {
  projectId: string
  featureId: string
}

/**
 * Retrieves all environments and their corresponding feature states for a given feature and project.
 * @param {string} featureId - The ID of the feature to retrieve environments and states for.
 * @param {string} projectId - The ID of the project containing the feature.
 */
export default function ({
  featureId,
  projectId,
}: {
  featureId: string | number | undefined
  projectId: string | number | undefined
}) {
  const [featureStates, setFeatureStates] = useState<
    {
      environment: Environment
      environmentFeatureState: FeatureState
      segmentOverrides: FeatureState[]
      identityOverrides: FeatureState[]
    }[]
  >()

  const { data: environments } = useGetEnvironmentsQuery(
    { projectId: `${projectId}` },
    { skip: !projectId },
  )
  useEffect(() => {
    setFeatureStates([])
    if (!environments || !featureId) {
      return
    }
    Promise.all(
      environments?.results.map((environment) => {
        return getFeatureStates(getStore(), {
          environmentAPIKey: environment.api_key,
          feature: featureId,
        }).then((res: { data: Res['featureStates'] }) => {
          return {
            environment,
            environmentFeatureState: res.data.results.find(
              (v) => !v.feature_segment && !v.identity,
            )!,
            identityOverrides: res.data.results.filter((v) => !!v.identity),
            segmentOverrides: res.data.results.filter(
              (v) => !!v.feature_segment,
            ),
          }
        })
      }),
    ).then((res) => {
      setFeatureStates(res)
    })
  }, [environments, featureId])
  return keyBy(featureStates, (v) => `${v.environment?.id}`)
}
