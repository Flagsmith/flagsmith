import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const organisationLicensingService = service
  .enhanceEndpoints({ addTagTypes: ['OrganisationLicensing'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      uploadOrganisationLicence: builder.mutation<
        Res['organisationLicence'],
        Req['uploadOrganisationLicence']
      >({
        query: (query: Req['uploadOrganisationLicence']) => {
          const formData = new FormData()
          formData.append('licence_signature', query.body.licence_signature)
          formData.append('licence', query.body.licence)
          return {
            body: formData,
            method: 'PUT',
            url: `organisations/${query.id}/licence`,
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function uploadOrganisationLicence(
  store: any,
  data: Req['uploadOrganisationLicence'],
  options?: Parameters<
    typeof organisationLicensingService.endpoints.uploadOrganisationLicence.initiate
  >[1],
) {
  store.dispatch(
    organisationLicensingService.endpoints.uploadOrganisationLicence.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(organisationLicensingService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useUploadOrganisationLicenceMutation,
  // END OF EXPORTS
} = organisationLicensingService
