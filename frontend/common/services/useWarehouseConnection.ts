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
        query: ({ environmentId, uuid }) => ({
          method: 'DELETE',
          url: `environments/${environmentId}/warehouse-connections/${uuid}/`,
        }),
      }),
      getWarehouseConnections: builder.query<
        Res['warehouseConnections'],
        Req['getWarehouseConnections']
      >({
        providesTags: [{ id: 'LIST', type: 'WarehouseConnection' }],
        query: ({ environmentId }) => ({
          url: `environments/${environmentId}/warehouse-connections/`,
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
  useUpdateWarehouseConnectionMutation,
} = warehouseConnectionService
