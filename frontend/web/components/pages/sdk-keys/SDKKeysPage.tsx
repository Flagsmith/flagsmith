import React, { FC } from 'react'
import CopyField from 'components/CopyField'
import PageTitle from 'components/PageTitle'
import Button from 'components/base/forms/Button'
import { useRouteMatch } from 'react-router-dom'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { ServerSideSDKKeys } from './components'

interface RouteParams {
  environmentId: string
  projectId: string
}

const SDKKeysPage: FC = () => {
  const match = useRouteMatch<RouteParams>()
  const environmentId = match?.params?.environmentId
  const projectId = match?.params?.projectId

  const { data: environments } = useGetEnvironmentsQuery(
    { projectId: parseInt(projectId, 10) },
    { skip: !projectId },
  )

  const environmentName =
    environments?.results?.find((env) => env.api_key === environmentId)?.name ??
    ''

  return (
    <div
      data-test='sdk-keys-page'
      id='sdk-keys-page'
      className='app-container container'
    >
      <PageTitle title='Client-side Environment Key'>
        Use this key to initialise{' '}
        <Button
          theme='text'
          href='https://docs.flagsmith.com/clients/overview#client-side-sdks'
          target='_blank'
        >
          Client-side
        </Button>{' '}
        SDKs.
      </PageTitle>
      <div className='col-md-6'>
        <CopyField value={environmentId} />
      </div>
      <hr className='py-0 my-4' />
      <ServerSideSDKKeys
        environmentId={environmentId}
        environmentName={environmentName}
      />
    </div>
  )
}

export default SDKKeysPage
