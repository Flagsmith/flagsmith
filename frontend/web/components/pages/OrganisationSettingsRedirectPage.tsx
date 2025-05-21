import { FC, useEffect } from 'react'
import { useHistory } from 'react-router'
import AccountStore from 'common/stores/account-store'
import ConfigProvider from 'common/providers/ConfigProvider'

const OrganisationSettingsRedirectPage: FC = () => {
  const history = useHistory()
  useEffect(() => {
    if (AccountStore.getOrganisation()) {
      history.replace(
        `/organisation/${AccountStore.getOrganisation().id}/settings${
          document.location.search
        }`,
      )
    } else {
      history.replace('/organisations')
    }
  }, [history])
  return (
    <div className='text-center'>
      <Loader />
    </div>
  )
}

export default ConfigProvider(OrganisationSettingsRedirectPage)
