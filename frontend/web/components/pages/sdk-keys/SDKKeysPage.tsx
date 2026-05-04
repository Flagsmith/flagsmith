import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import Icon from 'components/icons/Icon'
import PageTitle from 'components/PageTitle'
import Utils from 'common/utils/utils'
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

  const handleCopy = () => Utils.copyToClipboard(environmentId)

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
        <Row>
          <Flex>
            <Input
              value={environmentId}
              inputClassName='input input--wide'
              type='text'
              title={<h3>Client-side Environment Key</h3>}
              placeholder='Client-side Environment Key'
            />
          </Flex>
          <Button onClick={handleCopy} className='ml-2 btn-with-icon text-body'>
            <Icon name='copy' width={20} />
          </Button>
        </Row>
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
