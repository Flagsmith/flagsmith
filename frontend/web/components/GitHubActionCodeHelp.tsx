import React, { FC, useState } from 'react'
import Highlight from './Highlight'
import Constants from 'common/constants'
import { Clipboard } from 'polyfill-react-native'
import Icon from './Icon'
import { Button } from './base/forms/Button'

type GitHubActionCodeHelpType = {
  projectId: string
  title: string
}

const GitHubActionCodeHelp: FC<GitHubActionCodeHelpType> = ({
  projectId,
  title,
}) => {
  const [visible, setVisible] = useState(false)
  const copy = (s: string) => {
    const res = Clipboard.setString(s)
    toast(
      res ? 'Clipboard set' : 'Could not set clipboard :(',
      res ? '' : 'danger',
    )
  }

  return (
    <div className='mt-2'>
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
        <div>
          <div className='hljs-container'>
            <Highlight forceExpanded preventEscape>
              {Constants.codeHelp.gitHubActionsExample(projectId, Project.api)}
            </Highlight>
            <Column className='hljs-docs'>
              <Button
                onClick={() =>
                  copy(
                    Constants.codeHelp.gitHubActionsExample(
                      projectId,
                      Project.api,
                    ),
                  )
                }
                size='xSmall'
                iconLeft='copy'
                iconLeftColour='white'
              >
                Copy Code
              </Button>
            </Column>
          </div>
        </div>
      )}
    </div>
  )
}

export default GitHubActionCodeHelp
