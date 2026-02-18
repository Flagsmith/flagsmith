import { sortBy } from 'lodash'

import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import transformCorePaging from 'common/transformCorePaging'
import Utils from 'common/utils/utils'
import { CustomMetadataField } from 'common/types/metadata-field'
import {
  Environment,
  Metadata,
  MetadataField,
  PagedResponse,
  ProjectFlag,
  Segment,
} from 'common/types/responses'

type EntityType = 'feature' | 'segment' | 'environment'

type EntityMetadataParams = {
  organisationId: number
  projectId: number
  entityContentType: number
  entityType: EntityType
  entityId?: number
}

type EntityData = ProjectFlag | Segment | Environment

type EntityWithMetadata = {
  metadata?: Metadata[]
}

function getEntityUrl(params: EntityMetadataParams): string | null {
  const { entityId, entityType, projectId } = params

  switch (entityType) {
    case 'feature':
      return `projects/${projectId}/features/${entityId}/`
    case 'segment':
      return `projects/${projectId}/segments/${entityId}/`
    case 'environment':
      return `environments/${entityId}/`
    default:
      return null
  }
}

export const metadataService = service
  .enhanceEndpoints({ addTagTypes: ['Metadata'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createMetadataField: builder.mutation<
        Res['metadataField'],
        Req['createMetadataField']
      >({
        invalidatesTags: [{ type: 'Metadata' }],
        query: (query: Req['createMetadataField']) => ({
          body: query.body,
          method: 'POST',
          url: `metadata/fields/`,
        }),
      }),
      deleteMetadataField: builder.mutation<
        Res['metadataField'],
        Req['deleteMetadataField']
      >({
        invalidatesTags: [{ type: 'Metadata' }],
        query: (query: Req['deleteMetadataField']) => ({
          method: 'DELETE',
          url: `metadata/fields/${query.id}/`,
        }),
      }),
      getEntityMetadataFields: builder.query<
        CustomMetadataField[],
        EntityMetadataParams
      >({
        providesTags: (_res, _err, arg) => [
          {
            id: `${arg.entityType}-${arg.entityId ?? 'new'}-${
              arg.entityContentType
            }`,
            type: 'Metadata',
          },
        ],
        queryFn: async (arg, _api, _extraOptions, baseQuery) => {
          const entityUrl = getEntityUrl(arg)

          // Build queries to run in parallel
          const queries: Promise<{ data?: unknown; error?: unknown }>[] = [
            baseQuery({
              url: `projects/${arg.projectId}/metadata/fields/?${Utils.toParam({
                include_organisation: true,
              })}`,
            }),
          ]

          // Only fetch entity data if we have an entityId
          if (arg.entityId && entityUrl) {
            queries.push(baseQuery({ url: entityUrl }))
          }

          // Fetch all in parallel
          const results = await Promise.all(queries)

          const [fieldsRes, entityRes] = results

          // Handle errors
          if (fieldsRes.error) {
            return { error: fieldsRes.error as Res['metadataList'] }
          }

          if (entityRes?.error) {
            return { error: entityRes.error as EntityData }
          }

          const fieldList = fieldsRes.data as PagedResponse<MetadataField>
          const entityData = (entityRes?.data ??
            null) as EntityWithMetadata | null

          // Filter fields that apply to this content type using nested model_fields
          const fieldsForContentType: CustomMetadataField[] = fieldList.results
            .filter((meta) =>
              meta.model_fields.some(
                (mf) => mf.content_type === arg.entityContentType,
              ),
            )
            .map((meta) => {
              const matchingModelField = meta.model_fields.find(
                (mf) => mf.content_type === arg.entityContentType,
              )
              return {
                ...meta,
                isRequiredFor: !!matchingModelField?.is_required_for.length,
                metadataModelFieldId: matchingModelField
                  ? matchingModelField.id
                  : null,
              }
            })

          // Get existing values from the entity
          const existingValues: Metadata[] = entityData?.metadata ?? []

          // Merge field definitions with existing values
          const mergedMetadata = fieldsForContentType.map((field) => {
            const existingValue = existingValues.find(
              (v) => v.model_field === field.metadataModelFieldId,
            )
            return {
              ...field,
              field_value: existingValue?.field_value ?? '',
              hasValue: !!existingValue,
            }
          })

          return {
            data: sortBy(mergedMetadata, (m) => (m.isRequiredFor ? -1 : 1)),
          }
        },
      }),
      getMetadataField: builder.query<
        Res['metadataField'],
        Req['getMetadataField']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'Metadata' }],
        query: (query: Req['getMetadataField']) => ({
          url: `metadata/fields/${query.organisation_id}/`,
        }),
      }),
      getMetadataFieldList: builder.query<
        Res['metadataList'],
        Req['getMetadataList']
      >({
        providesTags: [{ id: 'LIST', type: 'Metadata' }],
        query: (query: Req['getMetadataList']) => ({
          url: `metadata/fields/?${Utils.toParam(query)}`,
        }),
        transformResponse: (res: Res['metadataList'], _, req) =>
          transformCorePaging(req, res),
      }),
      getProjectMetadataFieldList: builder.query<
        Res['projectMetadataFieldList'],
        Req['getProjectMetadataFieldList']
      >({
        providesTags: [{ id: 'LIST', type: 'Metadata' }],
        query: (query: Req['getProjectMetadataFieldList']) => ({
          url: `projects/${query.project_id}/metadata/fields/?${Utils.toParam({
            ...(query.include_organisation
              ? { include_organisation: true }
              : {}),
            page: query.page,
            page_size: query.page_size,
          })}`,
        }),
        transformResponse: (res: Res['projectMetadataFieldList'], _, req) =>
          transformCorePaging(req, res),
      }),
      updateMetadataField: builder.mutation<
        Res['metadataField'],
        Req['updateMetadataField']
      >({
        invalidatesTags: [{ type: 'Metadata' }],
        query: (query: Req['updateMetadataField']) => ({
          body: query.body,
          method: 'PUT',
          url: `metadata/fields/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createMetadataField(
  store: any,
  data: Req['createMetadataField'],
  options?: Parameters<
    typeof metadataService.endpoints.createMetadataField.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.createMetadataField.initiate(data, options),
  )
}
export async function deleteMetadataField(
  store: any,
  data: Req['deleteMetadataField'],
  options?: Parameters<
    typeof metadataService.endpoints.deleteMetadataField.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.deleteMetadataField.initiate(data, options),
  )
}
export async function getMetadata(
  store: any,
  data: Req['getMetadataField'],
  options?: Parameters<
    typeof metadataService.endpoints.getMetadataField.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.getMetadataField.initiate(data, options),
  )
}
export async function getMetadataList(
  store: any,
  data: Req['getMetadataList'],
  options?: Parameters<
    typeof metadataService.endpoints.getMetadataFieldList.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.getMetadataFieldList.initiate(data, options),
  )
}
export async function updateMetadata(
  store: any,
  data: Req['updateMetadataField'],
  options?: Parameters<
    typeof metadataService.endpoints.updateMetadataField.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.updateMetadataField.initiate(data, options),
  )
}
export async function getEntityMetadataFields(
  store: any,
  data: EntityMetadataParams,
  options?: Parameters<
    typeof metadataService.endpoints.getEntityMetadataFields.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.getEntityMetadataFields.initiate(data, options),
  )
}
export async function getProjectMetadataFieldList(
  store: any,
  data: Req['getProjectMetadataFieldList'],
  options?: Parameters<
    typeof metadataService.endpoints.getProjectMetadataFieldList.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.getProjectMetadataFieldList.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateMetadataFieldMutation,
  useDeleteMetadataFieldMutation,
  useGetEntityMetadataFieldsQuery,
  useGetMetadataFieldListQuery,
  useGetMetadataFieldQuery,
  useGetProjectMetadataFieldListQuery,
  useUpdateMetadataFieldMutation,
  // END OF EXPORTS
} = metadataService

/* Usage examples:
const { data, isLoading } = useGetMetadataFieldQuery({ id: 2 }, {}) //get hook
const [createMetadataField, { isLoading, data, isSuccess }] = useCreateMetadataFieldMutation() //create hook
metadataService.endpoints.getMetadataField.select({id: 2})(store.getState()) //access data from any function
*/
