import {
  FeatureState,
  FeatureVersion,
  PagedResponse,
  Res,
  Segment,
  TypedFeatureState,
} from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import { getStore } from 'common/store'
import { getVersionFeatureState } from './useVersionFeatureState'
import transformCorePaging from 'common/transformCorePaging'
import Utils from 'common/utils/utils'
import {
  getFeatureStateDiff,
  getSegmentDiff,
  getVariationDiff,
} from 'components/diff/diff-utils'
import { getSegments } from './useSegment'
import { getFeatureStates } from './useFeatureState'

const transformFeatureStates = (featureStates: TypedFeatureState[]) =>
  featureStates?.map((v) => ({
    ...v,
    feature_state_value: v.feature_state_value,
    id: undefined,
    multivariate_feature_state_values: v.multivariate_feature_state_values?.map(
      (v) => ({
        ...v,
        id: undefined,
      }),
    ),
  }))

export const getFeatureStateCrud = (
  featureStates: TypedFeatureState[],
  oldFeatureStates: TypedFeatureState[],
  segments?: Segment[] | null | undefined,
) => {
  const excludeNotChanged = (featureStates: TypedFeatureState[]) => {
    if (!oldFeatureStates) {
      return featureStates
    }
    const segmentDiffs = segments?.length
      ? getSegmentDiff(
          featureStates.filter((v) => !!v.feature_segment),
          oldFeatureStates.filter((v) => !!v.feature_segment),
          segments,
        )
      : null
    const featureStateDiffs = featureStates.filter((v) => {
      if (!v.feature_segment) return
      const diff = segmentDiffs?.diffs?.find(
        (diff) => v.feature_segment?.segment === diff.segment.id,
      )
      return !!diff?.totalChanges
    })
    const newValueFeatureState = featureStates.find((v) => !v.feature_segment)!
    const oldValueFeatureState = oldFeatureStates.find(
      (v) => !v.feature_segment,
    )!
    // return nothing if feature state isn't different
    const valueDiff = getFeatureStateDiff(
      oldValueFeatureState,
      newValueFeatureState,
    )
    if (!valueDiff.totalChanges) {
      const variationDiff = getVariationDiff(
        oldValueFeatureState,
        newValueFeatureState,
      )
      if (variationDiff.totalChanges) {
        featureStateDiffs.push(newValueFeatureState)
      }
    } else {
      featureStateDiffs.push(newValueFeatureState)
    }
    return featureStateDiffs
  }

  const featureStatesToCreate = featureStates.filter(
    (v) => !v.id && !v.toRemove,
  )
  const featureStatesToUpdate = excludeNotChanged(
    featureStates.filter((v) => !!v.id && !v.toRemove),
  )
  const segment_ids_to_delete_overrides: Req['createFeatureVersion']['segment_ids_to_delete_overrides'] =
    featureStates
      .filter((v) => !!v.id && !!v.toRemove && !!v.feature_segment)
      .map((v) => v.feature_segment!.segment)

  // Step 1: Create a new feature version
  const feature_states_to_create: Req['createFeatureVersion']['feature_states_to_create'] =
    transformFeatureStates(featureStatesToCreate)
  const feature_states_to_update: Req['createFeatureVersion']['feature_states_to_update'] =
    transformFeatureStates(featureStatesToUpdate)
  return {
    feature_states_to_create,
    feature_states_to_update,
    segment_ids_to_delete_overrides,
  }
}
export const featureVersionService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureVersion'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createAndSetFeatureVersion: builder.mutation<
        Res['featureVersion'],
        Req['createAndSetFeatureVersion']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureVersion' }],
        queryFn: async (query: Req['createAndSetFeatureVersion']) => {
          // todo: this will be removed when we combine saving value and segment overrides
          const mode = query.featureStates.find(
            (v) => !v.feature_segment?.segment,
          )
            ? 'VALUE'
            : 'SEGMENT'
          const oldFeatureStates: { data: PagedResponse<TypedFeatureState> } =
            await getFeatureStates(
              getStore(),
              {
                environment: query.environmentId,
                feature: query.featureId,
              },
              {
                forceRefetch: true,
              },
            )
          const segments =
            mode === 'VALUE'
              ? undefined
              : (
                  await getSegments(getStore(), {
                    include_feature_specific: true,
                    page_size: 1000,
                    projectId: query.projectId,
                  })
                ).data.results

          const {
            feature_states_to_create,
            feature_states_to_update,
            segment_ids_to_delete_overrides,
          } = getFeatureStateCrud(
            query.featureStates.map((v) => ({
              ...v,
              feature_state_value: Utils.valueToFeatureState(
                v.feature_state_value,
              ),
            })),
            oldFeatureStates.data.results.filter((v) => {
              if (mode === 'VALUE') {
                return !v.feature_segment?.segment
              } else {
                return !!v.feature_segment?.segment
              }
            }),
            segments,
          )

          if (
            !feature_states_to_create.length &&
            !feature_states_to_update.length &&
            !segment_ids_to_delete_overrides.length
          ) {
            throw new Error('Feature contains no changes')
          }

          const versionRes: { data: FeatureVersion } =
            await createFeatureVersion(getStore(), {
              environmentId: query.environmentId,
              featureId: query.featureId,
              feature_states_to_create,
              feature_states_to_update,
              live_from: query.liveFrom,
              publish_immediately: !query.skipPublish,
              segment_ids_to_delete_overrides,
            })

          const currentFeatureStates: { data: FeatureState[] } =
            await getVersionFeatureState(getStore(), {
              environmentId: query.environmentId,
              featureId: query.featureId,
              sha: versionRes.data.uuid,
            })

          const res = currentFeatureStates.data

          const ret = {
            error: res.find((v) => !!v.error)?.error,
            feature_states: res.map((item) => ({
              data: item,
              version_sha: versionRes.data.uuid,
            })),
            feature_states_to_create,
            feature_states_to_update,
            segment_ids_to_delete_overrides,
            version_sha: versionRes.data.uuid,
          }

          return { data: ret } as any
        },
      }),
      createFeatureVersion: builder.mutation<
        Res['featureVersion'],
        Req['createFeatureVersion']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureVersion' }],
        query: (query: Req['createFeatureVersion']) => ({
          body: query,
          method: 'POST',
          url: `environments/${query.environmentId}/features/${query.featureId}/versions/`,
        }),
      }),
      getFeatureVersion: builder.query<
        Res['featureVersion'],
        Req['getFeatureVersion']
      >({
        providesTags: (res) => [{ id: res?.uuid, type: 'FeatureVersion' }],
        query: (query: Req['getFeatureVersion']) => ({
          url: `environment-feature-versions/${query.uuid}/`,
        }),
      }),
      getFeatureVersions: builder.query<
        Res['featureVersions'],
        Req['getFeatureVersions']
      >({
        providesTags: [{ id: 'LIST', type: 'FeatureVersion' }],
        query: (query) => ({
          url: `environments/${query.environmentId}/features/${
            query.featureId
          }/versions/?${Utils.toParam(query)}`,
        }),
        transformResponse: (
          baseQueryReturnValue: Res['featureVersions'],
          meta,
          req,
        ) => {
          return transformCorePaging(req, baseQueryReturnValue)
        },
      }),
      publishFeatureVersion: builder.mutation<
        Res['featureVersion'],
        Req['publishFeatureVersion']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureVersion' }],
        query: (query: Req['publishFeatureVersion']) => ({
          body: query,
          method: 'POST',
          url: `environments/${query.environmentId}/features/${query.featureId}/versions/${query.sha}/publish/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createFeatureVersion(
  store: any,
  data: Req['createFeatureVersion'],
  options?: Parameters<
    typeof featureVersionService.endpoints.createFeatureVersion.initiate
  >[1],
) {
  return store.dispatch(
    featureVersionService.endpoints.createFeatureVersion.initiate(
      data,
      options,
    ),
  )
}
export async function publishFeatureVersion(
  store: any,
  data: Req['publishFeatureVersion'],
  options?: Parameters<
    typeof featureVersionService.endpoints.publishFeatureVersion.initiate
  >[1],
) {
  return store.dispatch(
    featureVersionService.endpoints.publishFeatureVersion.initiate(
      data,
      options,
    ),
  )
}
export async function createAndSetFeatureVersion(
  store: any,
  data: Req['createAndSetFeatureVersion'],
  options?: Parameters<
    typeof featureVersionService.endpoints.createAndSetFeatureVersion.initiate
  >[1],
) {
  return store.dispatch(
    featureVersionService.endpoints.createAndSetFeatureVersion.initiate(
      data,
      options,
    ),
  )
}
export async function getFeatureVersions(
  store: any,
  data: Req['getFeatureVersions'],
  options?: Parameters<
    typeof featureVersionService.endpoints.getFeatureVersions.initiate
  >[1],
) {
  return store.dispatch(
    featureVersionService.endpoints.getFeatureVersions.initiate(data, options),
  )
}
export async function getFeatureVersion(
  store: any,
  data: Req['getFeatureVersion'],
  options?: Parameters<
    typeof featureVersionService.endpoints.getFeatureVersion.initiate
  >[1],
) {
  return store.dispatch(
    featureVersionService.endpoints.getFeatureVersion.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateAndSetFeatureVersionMutation,
  useCreateFeatureVersionMutation,
  useGetFeatureVersionQuery,
  useGetFeatureVersionsQuery,
  // END OF EXPORTS
} = featureVersionService

/* Usage examples:
const { data, isLoading } = useGetFeatureVersionQuery({ id: 2 }, {}) //get hook
const [createFeatureVersion, { isLoading, data, isSuccess }] = useCreateFeatureVersionMutation() //create hook
featureVersionService.endpoints.getFeatureVersion.select({id: 2})(store.getState()) //access data from any function
*/
