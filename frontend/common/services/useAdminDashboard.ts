import { Req } from 'common/types/requests'
import { Res } from 'common/types/responses'
import { service } from 'common/service'

export const adminDashboardService = service
  .enhanceEndpoints({ addTagTypes: ['AdminDashboard'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getAdminDashboardMetrics: builder.query<
        Res['adminDashboardMetrics'],
        Req['getAdminDashboardMetrics']
      >({
        providesTags: [{ id: 'LIST', type: 'AdminDashboard' }],
        queryFn: async (query, _, _2, baseQuery) => {
          const daysParam = query.days ? `?days=${query.days}` : ''
          const [
            summaryRes,
            organisationsRes,
            usageTrendsRes,
            staleFlagsRes,
            integrationsRes,
            releasePipelinesRes,
          ] = await Promise.all([
            baseQuery({ url: `admin/dashboard/summary/${daysParam}` }),
            baseQuery({ url: `admin/dashboard/organisations/` }),
            baseQuery({ url: `admin/dashboard/usage-trends/${daysParam}` }),
            baseQuery({ url: `admin/dashboard/stale-flags/` }),
            baseQuery({ url: `admin/dashboard/integrations/` }),
            baseQuery({ url: `admin/dashboard/release-pipelines/` }),
          ])

          const erroredQuery = [
            summaryRes,
            organisationsRes,
            usageTrendsRes,
            staleFlagsRes,
            integrationsRes,
            releasePipelinesRes,
          ].find((v) => !!v?.error)

          if (erroredQuery) {
            return { error: erroredQuery.error }
          }

          return {
            data: {
              integration_breakdown:
                integrationsRes.data as Res['adminDashboardMetrics']['integration_breakdown'],
              organisations:
                organisationsRes.data as Res['adminDashboardMetrics']['organisations'],
              release_pipeline_stats:
                releasePipelinesRes.data as Res['adminDashboardMetrics']['release_pipeline_stats'],
              stale_flags_per_project:
                staleFlagsRes.data as Res['adminDashboardMetrics']['stale_flags_per_project'],
              summary:
                summaryRes.data as Res['adminDashboardMetrics']['summary'],
              usage_trends:
                usageTrendsRes.data as Res['adminDashboardMetrics']['usage_trends'],
            },
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getAdminDashboardMetrics(
  store: any,
  data: Req['getAdminDashboardMetrics'],
  options?: Parameters<
    typeof adminDashboardService.endpoints.getAdminDashboardMetrics.initiate
  >[1],
) {
  return store.dispatch(
    adminDashboardService.endpoints.getAdminDashboardMetrics.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetAdminDashboardMetricsQuery,
  // END OF EXPORTS
} = adminDashboardService
