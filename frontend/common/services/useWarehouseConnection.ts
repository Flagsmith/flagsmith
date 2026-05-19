import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const warehouseConnectionService = service
  .enhanceEndpoints({ addTagTypes: ['WarehouseConnection'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createWarehouseConnection: builder.mutation<
        Res['warehouseConnection'],
        Req['createWarehouseConnection']
      >({
        invalidatesTags: [{ id: 'SINGLETON', type: 'WarehouseConnection' }],
        query: ({ environmentId, ...body }) => ({
          body,
          method: 'POST',
          url: `environments/${environmentId}/warehouse-connection/`,
        }),
      }),
      deleteWarehouseConnection: builder.mutation<
        void,
        Req['deleteWarehouseConnection']
      >({
        invalidatesTags: [{ id: 'SINGLETON', type: 'WarehouseConnection' }],
        query: ({ environmentId }) => ({
          method: 'DELETE',
          url: `environments/${environmentId}/warehouse-connection/`,
        }),
      }),
      getWarehouseConnection: builder.query<
        Res['warehouseConnection'],
        Req['getWarehouseConnection']
      >({
        providesTags: [{ id: 'SINGLETON', type: 'WarehouseConnection' }],
        query: ({ environmentId }) => ({
          url: `environments/${environmentId}/warehouse-connection/`,
        }),
      }),
    }),
  })

export const {
  useCreateWarehouseConnectionMutation,
  useDeleteWarehouseConnectionMutation,
  useGetWarehouseConnectionQuery,
} = warehouseConnectionService
