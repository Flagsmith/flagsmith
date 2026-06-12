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
        async onQueryStarted({ environmentId }, { dispatch, queryFulfilled }) {
          const { data } = await queryFulfilled
          dispatch(
            warehouseConnectionService.util.updateQueryData(
              'getWarehouseConnections',
              { environmentId },
              () => [data],
            ),
          )
        },
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
  useTestWarehouseConnectionMutation,
  useUpdateWarehouseConnectionMutation,
} = warehouseConnectionService
