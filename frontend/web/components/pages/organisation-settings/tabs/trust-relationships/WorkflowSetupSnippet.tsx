import React, { FC, useMemo } from 'react'
import CodeCard from 'components/pages/onboarding/OnboardingConnectPanel/CodeCard'
import Icon from 'components/icons/Icon'
import { TrustRelationship } from 'common/types/responses'

export const GITHUB_ISSUER = 'https://token.actions.githubusercontent.com'

// Claims the GitHub form can round-trip; anything else edits as freeform.
const GITHUB_FORM_CLAIMS = ['repository', 'repository_id', 'environment']

export const isGithubFormEditable = (
  trustRelationship: TrustRelationship,
): boolean =>
  trustRelationship.issuer === GITHUB_ISSUER &&
  trustRelationship.claim_rules.every(
    (rule) =>
      GITHUB_FORM_CLAIMS.includes(rule.claim) && rule.values.length === 1,
  ) &&
  trustRelationship.claim_rules.some(
    (rule) => rule.claim === 'repository' || rule.claim === 'repository_id',
  )

const GITHUB_OWNER_AUDIENCE_REGEX = /^https:\/\/github\.com\/[^/]+$/

export const isDefaultGithubAudience = (audience: string): boolean =>
  GITHUB_OWNER_AUDIENCE_REGEX.test(audience)

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
