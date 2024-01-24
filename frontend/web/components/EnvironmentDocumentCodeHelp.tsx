import React, { FC, useState } from 'react'
import Constants from 'common/constants'
import CodeHelp from './CodeHelp'
import Icon from './Icon'
import Tabs from './base/forms/Tabs'
import TabItem from './base/forms/TabItem'
import InfoMessage from './InfoMessage'
import { useGetServersideEnvironmentKeysQuery } from 'common/services/useServersideEnvironmentKey'
type EnvironmentDocumentCodeHelpType = {
  environmentId: string
  title: string
}

const EnvironmentDocumentCodeHelp: FC<EnvironmentDocumentCodeHelpType> = ({
  environmentId,
  title,
}) => {
  const [visible, setVisible] = useState(false)
  const { data } = useGetServersideEnvironmentKeysQuery({ environmentId })
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
          <InfoMessage>
            <div>
              Providing flag defaults is recommended for{' '}
              <a
                target='_blank'
                href='https://docs.flagsmith.com/guides-and-examples/defensive-coding'
                rel='noreferrer'
              >
                defensive coding
              </a>{' '}
              and allowing offline capabilities.
              <br />
              By default SDKs run in remote evaluation mode, server-side SDKs
              can also run in local evaluation mode.{' '}
              <a
                target='_blank'
                href='https://docs.flagsmith.com/clients/overview'
                rel='noreferrer'
              >
                Check the Docs for more details
              </a>
              .
            </div>
          </InfoMessage>
          <Tabs uncontrolled theme='pill'>
            <TabItem tabLabel={'Remote Evaluation'}>
              <div className='mt-3'>
                <CodeHelp
                  hideHeader
                  snippets={Constants.codeHelp.OFFLINE_REMOTE(environmentId)}
                />
              </div>
            </TabItem>
            <TabItem tabLabel={'Local Evaluation'}>
              <div className='mt-3'>
                {data?.length ? (
                  <CodeHelp
                    hideHeader
                    snippets={Constants.codeHelp.OFFLINE_LOCAL(data?.[0]?.key)}
                  />
                ) : (
                  <InfoMessage>
                    In order to setup local evaluation mode you need at least 1
                    API key, this can be created in Environment Settings.
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
