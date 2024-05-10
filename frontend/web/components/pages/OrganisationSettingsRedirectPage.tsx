import { FC, useEffect } from 'react'
import { RouterChildContext } from 'react-router'
import AccountStore from 'common/stores/account-store'
import ConfigProvider from 'common/providers/ConfigProvider'

type OrganisationSettingsRedirectPageType = {
  router: RouterChildContext['router']
}

const OrganisationSettingsRedirectPage: FC<
  OrganisationSettingsRedirectPageType
> = ({ router }) => {
  useEffect(() => {
    if (AccountStore.getOrganisation()) {
      router.history.replace(
        `/organisation/${AccountStore.getOrganisation().id}/settings${
          document.location.search
        }`,
      )
    } else {
      router.history.replace('/organisations')
    }
  }, [])
  return (
    <div className='text-center'>
      <Loader />
    </div>
  )
}

export default ConfigProvider(OrganisationSettingsRedirectPage)
