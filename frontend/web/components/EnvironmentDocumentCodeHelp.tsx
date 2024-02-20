import React, { FC, useState } from 'react'
import Constants from 'common/constants'
import CodeHelp from './CodeHelp'
import Icon from './Icon'
import Tabs from './base/forms/Tabs'
import TabItem from './base/forms/TabItem'
import InfoMessage from './InfoMessage'
import { useGetServersideEnvironmentKeysQuery } from 'common/services/useServersideEnvironmentKey'
import { useHasPermission } from 'common/providers/Permission'
import { Link } from 'react-router-dom'
type EnvironmentDocumentCodeHelpType = {
  environmentId: string
  projectId: string
  title: string
}

const EnvironmentDocumentCodeHelp: FC<EnvironmentDocumentCodeHelpType> = ({
  environmentId,
  projectId,
  title,
}) => {
  const [visible, setVisible] = useState(false)
  const { data } = useGetServersideEnvironmentKeysQuery({ environmentId })
  const envAdmin = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: 'ADMIN',
  })
  return (
    <div>
      <div
        style={{ cursor: 'pointer' }}
        onClick={() => {
          setVisible(!visible)
        }}
      >
        <Row>
          <Flex style={isMobile ? { overflowX: 'scroll' } : {}}>
            <div>
              <pre className='hljs-header'>
                <span />
                {'<>'} Code example:{' '}
                <span className='hljs-description'>{title}</span>
                <span className='hljs-icon'>
                  <Icon
                    name={visible ? 'chevron-down' : 'chevron-right'}
                    width={16}
                  />
                </span>
              </pre>
            </div>
          </Flex>
        </Row>
      </div>
      {!!visible && (
        <div className='mt-2'>
          <div className='mb-2'>
            Providing flag defaults is recommended for{' '}
            <a
              className='text-primary'
              target='_blank'
              href='https://docs.flagsmith.com/guides-and-examples/defensive-coding'
              rel='noreferrer'
            >
              defensive coding
            </a>{' '}
            and allowing offline capabilities.
          </div>
          <Tabs uncontrolled theme='pill'>
            <TabItem tabLabel={'Client-side'}>
              <div className='mt-3'>
                <InfoMessage className='mb-2'>
                  <div>
                    This will not return any features marked as{' '}
                    <a
                      href={
                        'https://docs.flagsmith.com/advanced-use/flag-management#server-side-only-flags'
                      }
                      target={'_blank'}
                      rel='noreferrer'
                    >
                      server-side only
                    </a>
                    .
                  </div>
                </InfoMessage>
                <CodeHelp
                  hideHeader
                  snippets={Constants.codeHelp.OFFLINE_REMOTE(environmentId)}
                />
              </div>
            </TabItem>
            <TabItem tabLabel={'Server-side'}>
              <div className='mt-3'>
                {data?.length ? (
                  <CodeHelp
                    hideHeader
                    snippets={Constants.codeHelp.OFFLINE_LOCAL(data?.[0]?.key)}
                  />
                ) : (
                  <InfoMessage>
                    In order to setup local evaluation mode you need at least 1
                    API key, this can be created in{' '}
                    {envAdmin ? (
                      <Link
                        to={`/project/${projectId}/environment/${environmentId}/settings`}
                      >
                        Environment Settings
                      </Link>
                    ) : (
                      'Environment Settings. Please contact an environment administrator about this.'
                    )}
                    .
                  </InfoMessage>
                )}
              </div>
            </TabItem>
          </Tabs>
        </div>
      )}
    </div>
  )
}

export default EnvironmentDocumentCodeHelp
