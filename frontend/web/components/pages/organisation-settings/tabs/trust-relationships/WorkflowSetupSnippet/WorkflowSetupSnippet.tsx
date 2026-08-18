import React, { FC, useMemo } from 'react'
import CodeCard from 'components/pages/onboarding/OnboardingConnectPanel/CodeCard'
import Icon from 'components/icons/Icon'
import Project from 'common/project'
import { isDefaultGithubAudience } from 'components/pages/organisation-settings/tabs/trust-relationships/github'

const SAAS_API_URL = 'https://api.flagsmith.com'

// The CLI defaults to the SaaS API, so the snippet only needs an explicit
// api-url on other instances. It takes the base URL without /api/v1, which
// the CLI appends itself.
export const getNonDefaultApiUrl = (): string | undefined => {
  // Project.api can be relative, e.g. /api/v1/
  const resolved = new Request(Project.api).url
  const baseUrl = resolved.replace(/\/api\/v1\/?$/, '')
  return baseUrl === SAAS_API_URL ? undefined : baseUrl
}

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
    const withInputs: string[] = []
    if (!isDefaultAudience) {
      withInputs.push(`audience: ${audience}`)
    }
    const apiUrl = getNonDefaultApiUrl()
    if (apiUrl) {
      withInputs.push(`api-url: ${apiUrl}`)
    }
    if (withInputs.length) {
      lines.push(
        '        with:',
        ...withInputs.map((input) => `          ${input}`),
      )
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
