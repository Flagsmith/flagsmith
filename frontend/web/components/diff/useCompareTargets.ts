import { useEffect, useMemo, useState } from 'react'
import { getStore } from 'common/store'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import { getFeatureStates } from 'common/services/useFeatureState'
import {
  FeatureState,
  FeatureStateValue,
  FlagsmithValue,
} from 'common/types/responses'
import Utils from 'common/utils/utils'

export type CompareTarget = {
  label: string
  group: string
  enabled: boolean
  value: FlagsmithValue
}

export type CompareSource =
  | { kind: 'environment' }
  | { kind: 'segment'; segmentId: number }

type UseCompareTargetsParams = {
  projectId: number | string
  // api_key of the environment the comparison is initiated from
  environmentId: string
  featureId: number
  source: CompareSource
}

// Builds the list of comparison targets for a feature: the current
// environment's default value and segment overrides, plus every other
// environment's default value and its override for the same segment (when one
// exists). Other environments' feature states are fetched imperatively since
// RTK Query hooks cannot be called in a loop.
const useCompareTargets = ({
  environmentId,
  featureId,
  projectId,
  source,
}: UseCompareTargetsParams): {
  targets: CompareTarget[]
  isLoading: boolean
} => {
  const { data: environments } = useGetEnvironmentsQuery({
    projectId: Number(projectId),
  })
  const { data: segments } = useGetSegmentsQuery({
    include_feature_specific: true,
    page_size: 1000,
    projectId: Number(projectId),
  })

  const [statesByEnv, setStatesByEnv] = useState<
    Record<number, FeatureState[]>
  >({})
  const [isLoading, setIsLoading] = useState(true)

  const envResults = environments?.results
  const sourceKind = source.kind
  const sourceSegmentId = source.kind === 'segment' ? source.segmentId : null

  useEffect(() => {
    let cancelled = false
    if (!envResults || !featureId) {
      // Environments still loading — stay in the loading state.
      return
    }
    if (!envResults.length) {
      setIsLoading(false)
      return
    }
    setIsLoading(true)
    Promise.all(
      envResults.map((env) =>
        getFeatureStates(getStore(), {
          environment: env.id,
          feature: featureId,
        })
          .then((res) => ({ id: env.id, results: res?.data?.results || [] }))
          .catch(() => ({ id: env.id, results: [] as FeatureState[] })),
      ),
    ).then((all) => {
      if (cancelled) {
        return
      }
      const next: Record<number, FeatureState[]> = {}
      all.forEach(({ id, results }) => {
        next[id] = results
      })
      setStatesByEnv(next)
      setIsLoading(false)
    })
    return () => {
      cancelled = true
    }
  }, [envResults, featureId])

  const targets = useMemo<CompareTarget[]>(() => {
    if (!envResults?.length) {
      return []
    }
    // Until the segments have loaded, show an ellipsis rather than the raw id.
    const segmentName = (segmentId: number) => {
      if (!segments?.results) {
        return '…'
      }
      return (
        segments.results.find((s) => s.id === segmentId)?.name ||
        `Segment ${segmentId}`
      )
    }
    // The featurestates endpoint returns feature_state_value as a typed
    // object, so convert it to a primitive before comparing/rendering.
    const toValue = (fs: FeatureState): FlagsmithValue =>
      Utils.featureStateToValue(
        fs.feature_state_value as unknown as FeatureStateValue,
      ) ?? null

    const out: CompareTarget[] = []
    // Targets are grouped by type: every environment's default sits under
    // "Environment Defaults", every segment override under "Segment
    // Overrides". Each label carries its environment name so it is searchable.
    const fromEnvironment = sourceKind === 'environment'
    const pushEnv = (env: { id: number; name: string }, isCurrent: boolean) => {
      const states = statesByEnv[env.id] || []
      // Environment default value (skip when it is the comparison source).
      if (!(isCurrent && fromEnvironment)) {
        const def = states.find((s) => !s.feature_segment?.segment)
        if (def) {
          out.push({
            enabled: !!def.enabled,
            group: 'Environment Defaults',
            label: env.name,
            value: toValue(def),
          })
        }
      }
      // Segment overrides. The current environment contributes all of its
      // overrides except the comparison source; other environments contribute
      // only the same segment's override.
      states.forEach((s) => {
        const segId = s.feature_segment?.segment
        if (!segId) {
          return
        }
        const include = isCurrent
          ? segId !== sourceSegmentId
          : sourceSegmentId !== null && segId === sourceSegmentId
        if (!include) {
          return
        }
        out.push({
          enabled: !!s.enabled,
          group: 'Segment Overrides',
          // Only other environments need the environment name to disambiguate;
          // the current environment's overrides stand on their own.
          label: isCurrent
            ? segmentName(segId)
            : `${env.name} › ${segmentName(segId)}`,
          value: toValue(s),
        })
      })
    }

    const currentEnv = envResults.find((e) => e.api_key === environmentId)
    if (currentEnv) {
      pushEnv(currentEnv, true)
    }
    envResults
      .filter((e) => e.api_key !== environmentId)
      .forEach((e) => pushEnv(e, false))
    return out
  }, [
    envResults,
    statesByEnv,
    segments,
    environmentId,
    sourceKind,
    sourceSegmentId,
  ])

  return { isLoading: isLoading || !segments?.results, targets }
}

export default useCompareTargets
