import { TrustRelationship } from 'common/types/responses'

export const GITHUB_ISSUER = 'https://token.actions.githubusercontent.com'
export const GITHUB_LABEL = 'GitHub Actions'

// Claims the GitHub form can round-trip; anything else edits as freeform.
const GITHUB_FORM_CLAIMS = [
  'repository',
  'repository_id',
  'environment',
  'workflow_ref',
]

// The repository rule already pins the repository, so the workflow rule only
// needs to enforce the path — a wildcard prefix survives repository renames,
// and the wildcard ref leaves branch filtering to the environment rule.
export const githubWorkflowRefPattern = (filename: string): string =>
  `*/.github/workflows/${filename}@*`

const GITHUB_WORKFLOW_REF_REGEX = /^\*\/\.github\/workflows\/(.+)@\*$/

export const parseGithubWorkflowFilename = (
  workflowRef: string | undefined,
): string | undefined =>
  workflowRef ? GITHUB_WORKFLOW_REF_REGEX.exec(workflowRef)?.[1] : undefined

export const isGithubFormEditable = (
  trustRelationship: TrustRelationship,
): boolean => {
  const claims = trustRelationship.claim_rules.map((rule) => rule.claim)
  // The form writes back one repository rule and one environment rule, so
  // anything it can't represent one-to-one has to edit as freeform — saving it
  // here would silently drop rules and widen the trust.
  const repositorySelectors = claims.filter(
    (claim) => claim === 'repository' || claim === 'repository_id',
  )
  return (
    trustRelationship.issuer === GITHUB_ISSUER &&
    new Set(claims).size === claims.length &&
    repositorySelectors.length === 1 &&
    trustRelationship.claim_rules.every(
      (rule) =>
        GITHUB_FORM_CLAIMS.includes(rule.claim) &&
        rule.values.length === 1 &&
        (rule.claim !== 'workflow_ref' ||
          !!parseGithubWorkflowFilename(rule.values[0])),
    )
  )
}

const GITHUB_OWNER_AUDIENCE_REGEX = /^https:\/\/github\.com\/[^/]+$/

export const isDefaultGithubAudience = (audience: string): boolean =>
  GITHUB_OWNER_AUDIENCE_REGEX.test(audience)
