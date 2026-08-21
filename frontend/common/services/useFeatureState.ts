import {
  FeatureState,
  FlagsmithValue,
  PagedResponse,
  ProjectFlag,
  Res,
  TypedFeatureState,
} from 'common/types/responses'
import { Req, UpdateFeatureValue } from 'common/types/requests'
import { service } from 'common/service'
import Project from 'common/project'
import Utils from 'common/utils/utils'
import { getFeatureSegment } from './useFeatureSegment'
import { createAndSetFeatureVersion } from './useFeatureVersion'
import { recursivePageGet } from 'common/utils/recursivePageGet'
import { getStore } from 'common/store'

// The consolidated update-flag endpoints (#7641) live under /api/experiments/
// rather than /api/v1/, so we build absolute URLs.
const experimentsApi = Project.api.replace(/v1\/$/, 'experiments/')

// Converts a feature value to the consolidated endpoint's payload shape,
// detecting the type the same way as the legacy valueToFeatureState (e.g.
// the string '42' is an integer). Returns null when the value cannot be
// represented (the endpoints have no way to express a null value).
export const toUpdateFeatureValue = (
  value: FlagsmithValue,
): UpdateFeatureValue | null => {
  if (value === null || value === undefined) {
    return null
  }
  const typedValue = Utils.getTypedValue(value, undefined, true)
  if (typeof typedValue === 'boolean') {
    return { type: 'boolean', value: String(typedValue) }
  }
  if (typeof typedValue === 'number') {
    return { type: 'integer', value: String(typedValue) }
  }
  return { type: 'string', value: String(typedValue) }
}

// Whether a feature update can go through the consolidated update-flag
// endpoint instead of the legacy versioned/non-versioned paths. Legacy is
// required when:
// - the feature is multivariate — not supported by the endpoint yet (#7642)
// - any value involved is null — the endpoint cannot represent null values
//
// Change-request environments are not checked here: such edits are routed to
// the change-request flow upstream (the FeatureListProvider action split and
// FeatureRow.onChange gate), so this is only ever reached for direct, non-CR
// edits. Reaching it in a workflow environment would be a caller bug.
export const canUseConsolidatedFeatureUpdate = ({
  projectFlag,
  values,
}: {
  projectFlag: ProjectFlag
  values: FlagsmithValue[]
}): boolean => {
  if (projectFlag.multivariate_options?.length) {
    return false
  }
  return values.every((value) => toUpdateFeatureValue(value) !== null)
}

export const addFeatureSegmentsToFeatureStates = async (v) => {
  if (typeof v.feature_segment !== 'number') {
    return v
  }
  const featureSegmentData = await getFeatureSegment(getStore(), {
    id: v.feature_segment,
  })
  return {
    ...v,
    feature_segment: featureSegmentData.data,
  }
}
export const featureStateService = service
  .enhanceEndpoints({
    addTagTypes: [
      'FeatureState',
      'FeatureList',
      'FeatureVersion',
      'Environment',
      'ProjectFlag',
    ],
  })
  .injectEndpoints({
    endpoints: (builder) => ({
      getAllEnvironmentFeatureStates: builder.query<
        Res['featureStates'],
        Req['getAllEnvironmentFeatureStates']
      >({
        providesTags: [{ id: 'LIST', type: 'FeatureState' }],
        queryFn: async (query, _baseQueryApi, _extraOptions, baseQuery) =>
          recursivePageGet<FeatureState>(
            `environments/${query.environmentKey}/featurestates/?page_size=999`,
            null,
            baseQuery,
          ),
      }),
      getFeatureStates: builder.query<
        Res['featureStates'],
        Req['getFeatureStates']
      >({
        providesTags: [{ id: 'LIST', type: 'FeatureState' }],
        queryFn: async (query, baseQueryApi, extraOptions, baseQuery) => {
          const {
            data,
          }: {
            data: PagedResponse<
              Omit<FeatureState, 'feature_segment'> & {
                feature_segment: number | null
              }
            >
          } = await baseQuery({
            url: `features/featurestates/?${Utils.toParam(query)}`,
          })
          const results = await Promise.all(
            data.results.map(addFeatureSegmentsToFeatureStates),
          )
          return {
            data: {
              ...data,
              results,
            },
          }
        },
      }),
      // Composite mutation — toggles a feature's environment default
      // enabled state via updateFeature when eligible, falling back to the
      // legacy paths internally. The inner mutations handle cache
      // invalidation.
      toggleFeature: builder.mutation<
        Res['toggleFeature'],
        Req['toggleFeature']
      >({
        queryFn: async (
          query,
          baseQueryApi,
        ): Promise<{ data: Res['toggleFeature'] } | { error: any }> => {
          try {
            await toggleFeatureStates(
              { dispatch: baseQueryApi.dispatch },
              query,
            )
            return { data: undefined }
          } catch (error) {
            return { error: error as any }
          }
        },
      }),
      // Supersedes updateFeatureState and createAndSetFeatureVersion for
      // eligible updates — saves a feature's environment default and segment
      // overrides through the consolidated update endpoint (#7641) in a
      // single call, regardless of whether the environment uses feature
      // versioning. Removed overrides are deleted first (the endpoint merges
      // rather than replaces), and since the endpoint returns 204 No
      // Content, the live feature states are refetched afterwards.
      //
      // Returns { saved: false } when the update is not eligible —
      // callers should fall back to the legacy update paths (multivariate
      // flags until #7642, null values).
      updateFeature: builder.mutation<
        Res['updateFeature'],
        Req['updateFeature']
      >({
        invalidatesTags: (res, _meta, arg) =>
          res?.saved
            ? [
                {
                  id: `${arg.projectFlag.project}-${arg.environment.id}`,
                  type: 'FeatureList',
                },
                { id: 'LIST', type: 'FeatureState' },
                { id: 'LIST', type: 'FeatureVersion' },
                { id: 'METRICS', type: 'Environment' },
              ]
            : [],
        queryFn: async (
          query,
          baseQueryApi,
          extraOptions,
          baseQuery,
        ): Promise<{ data: Res['updateFeature'] } | { error: any }> => {
          const { environment, environmentDefault, projectFlag } = query
          if (
            !canUseConsolidatedFeatureUpdate({
              projectFlag,
              values: [
                environmentDefault.value,
                ...(query.segmentOverrides || []).map(
                  (override) => override.value,
                ),
              ],
            })
          ) {
            return { data: { saved: false } }
          }

          const deleteResults = await Promise.all(
            (query.removeSegmentIds || []).map((segmentId) =>
              baseQuery({
                body: {
                  feature: { id: projectFlag.id },
                  segment: { id: segmentId },
                },
                method: 'POST',
                url: `${experimentsApi}environments/${environment.api_key}/delete-segment-override/`,
              }),
            ),
          )
          const deleteError = deleteResults.find((res) => res.error)
          if (deleteError?.error) {
            return { error: deleteError.error }
          }

          const updateRes = await baseQuery({
            body: {
              environment_default: {
                enabled: environmentDefault.enabled,
                value: toUpdateFeatureValue(environmentDefault.value)!,
              },
              feature: { id: projectFlag.id },
              segment_overrides: query.segmentOverrides?.map((override) => ({
                enabled: override.enabled,
                priority: override.priority,
                segment_id: override.segmentId,
                value: toUpdateFeatureValue(override.value)!,
              })),
            },
            method: 'POST',
            url: `${experimentsApi}environments/${environment.api_key}/update-flag-v2/`,
          })
          if (updateRes.error) {
            return { error: updateRes.error }
          }

          const statesRes: { data?: Res['featureStates'] } =
            await getFeatureStates(
              { dispatch: baseQueryApi.dispatch },
              {
                environment: environment.id,
                feature: projectFlag.id,
              },
              { forceRefetch: true },
            )
          return {
            data: {
              environmentDefault: statesRes.data?.results?.find(
                (v) => !v.feature_segment,
              ) as TypedFeatureState | undefined,
              saved: true,
            },
          }
        },
      }),
      /**
       * @deprecated Legacy update path for non-versioned environments.
       * Eligible updates go through the updateFeature mutation above
       * (#7641); this remains for multivariate flags (until #7642), null
       * flag values and identity overrides.
       */
      updateFeatureState: builder.mutation<
        Res['featureState'],
        Req['updateFeatureState']
      >({
        invalidatesTags: (_res, _meta, _req) => [
          { id: 'LIST', type: 'FeatureList' },
          { id: 'LIST', type: 'FeatureState' },
          { id: 'METRICS', type: 'Environment' },
          { type: 'ProjectFlag' },
        ],
        query: (query: Req['updateFeatureState']) => ({
          body: query.body,
          method: 'PUT',
          url: `environments/${query.environmentId}/featurestates/${query.environmentFlagId}/`,
        }),
      }),
    }),
  })

export async function getFeatureStates(
  store: any,
  data: Req['getFeatureStates'],
  options?: Parameters<
    typeof featureStateService.endpoints.getFeatureStates.initiate
  >[1],
) {
  return store.dispatch(
    featureStateService.endpoints.getFeatureStates.initiate(data, options),
  )
}

/**
 * @deprecated Legacy update path — prefer updateFeature (#7641). Remains
 * for multivariate flags (until #7642), null flag values and identity
 * overrides.
 */
export async function updateFeatureState(
  store: any,
  data: Req['updateFeatureState'],
  options?: Parameters<
    typeof featureStateService.endpoints.updateFeatureState.initiate
  >[1],
) {
  return store.dispatch(
    featureStateService.endpoints.updateFeatureState.initiate(data, options),
  )
}

export async function updateFeature(
  store: any,
  data: Req['updateFeature'],
  options?: Parameters<
    typeof featureStateService.endpoints.updateFeature.initiate
  >[1],
) {
  return store.dispatch(
    featureStateService.endpoints.updateFeature.initiate(data, options),
  )
}

// Toggles a feature's environment default enabled state. Uses the
// consolidated update endpoint (#7641) when eligible; otherwise falls back
// to the legacy versioned/non-versioned paths internally so callers have a
// single entry point. Exposed as the toggleFeature mutation above.
async function toggleFeatureStates(
  store: any,
  { environment, environmentFlag, projectFlag }: Req['toggleFeature'],
): Promise<void> {
  const enabled = !environmentFlag.enabled

  const updateRes = await updateFeature(store, {
    environment,
    environmentDefault: {
      enabled,
      value: environmentFlag.feature_state_value,
    },
    projectFlag,
  })
  if (updateRes.error) {
    throw updateRes.error
  }
  if (updateRes.data?.saved) {
    return
  }

  // Legacy fallbacks — multivariate flags (until #7642) and null flag values
  if (environment.use_v2_feature_versioning) {
    const versionRes = await createAndSetFeatureVersion(store, {
      environmentApiKey: environment.api_key,
      environmentId: environment.id,
      featureId: projectFlag.id,
      featureStates: [
        {
          ...environmentFlag,
          enabled,
        },
      ],
      projectId: projectFlag.project,
    })
    if (versionRes.error) {
      throw versionRes.error
    }
    return
  }

  const stateRes = await updateFeatureState(store, {
    body: { enabled },
    environmentFlagId: environmentFlag.id,
    environmentId: environment.api_key,
  })
  if (stateRes.error) {
    throw stateRes.error
  }
}

export const {
  useGetAllEnvironmentFeatureStatesQuery,
  useGetFeatureStatesQuery,
  useToggleFeatureMutation,
  useUpdateFeatureMutation,
  useUpdateFeatureStateMutation,
} = featureStateService
