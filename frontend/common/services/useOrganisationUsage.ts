import { Res } from 'common/types/responses';
import { Req } from 'common/types/requests';
import { service } from 'common/service';
import Utils from 'common/utils/utils';

export const organisationUsageService = service
    .enhanceEndpoints({ addTagTypes: ['OrganisationUsage'] })
    .injectEndpoints({
        endpoints: builder => ({

            getOrganisationUsage: builder.query<Res['organisationUsage'], Req['getOrganisationUsage']>({
                query: (query: Req['getOrganisationUsage']) => ({
                    url: `organisations/${query.organisationId}/influx-data/?${Utils.toParam({ project_id: query.projectId, environment_id: query.environmentId })}/`,
                }),
                transformResponse: (data: Res['organisationUsage']) => {
                    let flags = 0;
                    let traits = 0;
                    let environmentDocument = 0;
                    let identities = 0;
                    if (data?.events_list) { // protect against influx setup incorrectly
                        data.events_list.map((v) => {
                            environmentDocument += v['Environment-document'] || 0;
                            flags += v.Flags || 0;
                            traits += v.Traits || 0;
                            identities += v.Identities || 0;
                        });
                    }
                    return {
                        ...data,
                        totals: {
                            flags,
                            environmentDocument,
                            identities,
                            traits,
                            total: flags + traits + environmentDocument + identities,
                        },
                    };
                },
                providesTags: () => [{ type: 'OrganisationUsage', id: 'LIST' }],
            }),
            // END OF ENDPOINTS
        }),
    });

export async function getOrganisationUsage(store: any, data: Req['getOrganisationUsage'], options?: Parameters<typeof organisationUsageService.endpoints.getOrganisationUsage.initiate>[1]) {
    store.dispatch(organisationUsageService.endpoints.getOrganisationUsage.initiate(data, options));
    return Promise.all(store.dispatch(organisationUsageService.util.getRunningQueriesThunk()));
}
// END OF FUNCTION_EXPORTS

export const {
    useGetOrganisationUsageQuery,
    // END OF EXPORTS
} = organisationUsageService;

/* Usage examples:
const { data, isLoading } = useGetOrganisationUsageQuery({ id: 2 }, {}) //get hook
const [createOrganisationUsage, { isLoading, data, isSuccess }] = useCreateOrganisationUsageMutation() //create hook
organisationUsageService.endpoints.getOrganisationUsage.select({id: 2})(store.getState()) //access data from any function
*/
