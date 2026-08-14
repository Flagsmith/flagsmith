import React, { FC, useMemo } from 'react'
import CodeCard from 'components/pages/onboarding/OnboardingConnectPanel/CodeCard'
import Icon from 'components/icons/Icon'
import { isDefaultGithubAudience } from 'components/pages/organisation-settings/tabs/trust-relationships/github'

type WorkflowSetupSnippetProps = {
  audience: string
  environment?: string
}

const WorkflowSetupSnippet: FC<WorkflowSetupSnippetProps> = ({
  audience,
  environment,
}) => {
  const isDefaultAudience = isDefaultGithubAudience(audience)
  const code = useMemo(() => {
    const lines = ['jobs:', '  flagsmith:', '    runs-on: ubuntu-latest']
    if (environment) {
      lines.push(`    environment: ${environment}`)
    }
    lines.push(
      '    permissions:',
      '      id-token: write',
      '    steps:',
      '      - uses: Flagsmith/setup-cli@v1',
    )
    if (!isDefaultAudience) {
      lines.push('        with:', `          audience: ${audience}`)
    }
    return lines.join('\n')
  }, [environment, isDefaultAudience, audience])

  const header = <strong className='fs-small'>Workflow setup</strong>
  return (
    <div className='mt-3'>
      <CodeCard
        code={code}
        language='yaml'
        copyLabel='Copy workflow setup'
        headerLeft={
          isDefaultAudience ? (
            header
          ) : (
            <Tooltip
              title={
                <Row className='gap-1 align-items-center flex-nowrap'>
                  {header}
                  <Icon name='info-outlined' />
                </Row>
              }
            >
              {
                'The default audience for this owner is already in use, so the workflow must request this audience explicitly.'
              }
            </Tooltip>
          )
        }
      />
    </div>
  )
}

export default WorkflowSetupSnippet
