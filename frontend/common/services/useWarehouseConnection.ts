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
        query: ({ environmentId }) => ({
          url: `environments/${environmentId}/warehouse-connections/`,
        }),
      }),
    }),
  })

export const {
  useCreateWarehouseConnectionMutation,
  useDeleteWarehouseConnectionMutation,
  useGetWarehouseConnectionsQuery,
} = warehouseConnectionService
