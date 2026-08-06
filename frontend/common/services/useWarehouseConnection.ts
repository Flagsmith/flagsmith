import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const warehouseConnectionService = service
  .enhanceEndpoints({ addTagTypes: ['WarehouseConnection'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createWarehouseConnection: builder.mutation<
        Res['warehouseConnections'][number],
        Req['createWarehouseConnection']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'WarehouseConnection' }],
        query: ({ environmentId, ...body }) => ({
          body,
          method: 'POST',
          url: `environments/${environmentId}/warehouse-connections/`,
        }),
      }),
      deleteWarehouseConnection: builder.mutation<
        void,
        Req['deleteWarehouseConnection']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'WarehouseConnection' }],
        query: ({ environmentId, id }) => ({
          method: 'DELETE',
          url: `environments/${environmentId}/warehouse-connections/${id}/`,
        }),
      }),
      getWarehouseConnections: builder.query<
        Res['warehouseConnections'],
        Req['getWarehouseConnections']
      >({
        providesTags: [{ id: 'LIST', type: 'WarehouseConnection' }],
        query: ({ environmentId, exclude_event_stats }) => ({
          url: `environments/${environmentId}/warehouse-connections/${
            exclude_event_stats ? '?exclude_event_stats=true' : ''
          }`,
        }),
      }),
      testWarehouseConnection: builder.mutation<
        Res['warehouseConnections'][number],
        Req['testWarehouseConnection']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'WarehouseConnection' }],
        query: ({ environmentId, id }) => ({
          method: 'POST',
          url: `environments/${environmentId}/warehouse-connections/${id}/test-warehouse-connection/`,
        }),
      }),
      testWarehouseConnectionConfig: builder.mutation<
        Res['warehouseConnectionTestResult'],
        Req['testWarehouseConnectionConfig']
      >({
        query: ({ environmentId, ...body }) => ({
          body,
          method: 'POST',
          url: `environments/${environmentId}/warehouse-connections/test-warehouse-connection/`,
        }),
      }),
      updateWarehouseConnection: builder.mutation<
        Res['warehouseConnections'][number],
        Req['updateWarehouseConnection']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'WarehouseConnection' }],
        query: ({ environmentId, id, ...body }) => ({
          body,
          method: 'PATCH',
          url: `environments/${environmentId}/warehouse-connections/${id}/`,
        }),
      }),
    }),
  })

export const {
  useCreateWarehouseConnectionMutation,
  useDeleteWarehouseConnectionMutation,
  useGetWarehouseConnectionsQuery,
  useTestWarehouseConnectionConfigMutation,
  useTestWarehouseConnectionMutation,
  useUpdateWarehouseConnectionMutation,
} = warehouseConnectionService
