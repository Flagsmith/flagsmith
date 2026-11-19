import { FC, useEffect } from 'react'
import { useHistory } from 'react-router-dom'
import { useCurrentOrganisation } from 'common/hooks/useCurrentOrganisation'
import ConfigProvider from 'common/providers/ConfigProvider'

const OrganisationSettingsRedirectPage: FC = () => {
  const organisation = useCurrentOrganisation()
  const history = useHistory()
  useEffect(() => {
    if (organisation) {
      history.replace(
        `/organisation/${organisation.id}/settings${document.location.search}`,
      )
    } else {
      history.replace('/organisations')
    }
  }, [history, organisation])
  return (
    <div className='text-center'>
      <Loader />
    </div>
  )
}

export default ConfigProvider(OrganisationSettingsRedirectPage)
