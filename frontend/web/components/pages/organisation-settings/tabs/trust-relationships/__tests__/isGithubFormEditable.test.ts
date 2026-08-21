import {
  GITHUB_ISSUER,
  githubWorkflowRefPattern,
  isGithubFormEditable,
  parseGithubWorkflowFilename,
} from 'components/pages/organisation-settings/tabs/trust-relationships/github'
import {
  TrustRelationship,
  TrustRelationshipClaimRule,
} from 'common/types/responses'

const trustRelationship = (
  claimRules: TrustRelationshipClaimRule[],
  issuer = GITHUB_ISSUER,
) =>
  ({
    claim_rules: claimRules,
    issuer,
  } as TrustRelationship)

const REPOSITORY: TrustRelationshipClaimRule = {
  claim: 'repository',
  values: ['Flagsmith/flagsmith'],
}
const REPOSITORY_ID: TrustRelationshipClaimRule = {
  claim: 'repository_id',
  values: ['1234'],
}
const ENVIRONMENT: TrustRelationshipClaimRule = {
  claim: 'environment',
  values: ['production'],
}
const WORKFLOW_REF: TrustRelationshipClaimRule = {
  claim: 'workflow_ref',
  values: [githubWorkflowRefPattern('deploy.yml')],
}
const FOREIGN_WORKFLOW_REF: TrustRelationshipClaimRule = {
  claim: 'workflow_ref',
  values: ['Flagsmith/flagsmith/.github/workflows/deploy.yml@refs/heads/main'],
}

describe('isGithubFormEditable', () => {
  it.each`
    description                         | claimRules                                           | expected
    ${'a single repository rule'}       | ${[REPOSITORY]}                                      | ${true}
    ${'a repository and environment'}   | ${[REPOSITORY, ENVIRONMENT]}                         | ${true}
    ${'a repository pinned by id'}      | ${[REPOSITORY_ID]}                                   | ${true}
    ${'a workflow filename rule'}       | ${[REPOSITORY, WORKFLOW_REF]}                        | ${true}
    ${'a foreign workflow_ref rule'}    | ${[REPOSITORY, FOREIGN_WORKFLOW_REF]}                | ${false}
    ${'no repository selector'}         | ${[ENVIRONMENT]}                                     | ${false}
    ${'both repository selectors'}      | ${[REPOSITORY, REPOSITORY_ID]}                       | ${false}
    ${'a duplicated claim'}             | ${[REPOSITORY, ENVIRONMENT, ENVIRONMENT]}            | ${false}
    ${'a claim the form cannot render'} | ${[REPOSITORY, { claim: 'ref', values: ['main'] }]}  | ${false}
    ${'a rule with several values'}     | ${[{ claim: 'repository', values: ['a/b', 'c/d'] }]} | ${false}
  `('returns $expected for $description', ({ claimRules, expected }) => {
    // Given / When / Then
    expect(isGithubFormEditable(trustRelationship(claimRules))).toBe(expected)
  })

  it('returns false for a non-GitHub issuer', () => {
    // Given
    const relationship = trustRelationship([REPOSITORY], 'https://gitlab.com')

    // When / Then
    expect(isGithubFormEditable(relationship)).toBe(false)
  })
})

describe('parseGithubWorkflowFilename', () => {
  it('round-trips a pattern written by the form', () => {
    // Given
    const pattern = githubWorkflowRefPattern('deploy.yml')

    // When / Then
    expect(parseGithubWorkflowFilename(pattern)).toBe('deploy.yml')
  })

  it.each`
    description               | workflowRef
    ${'an undefined value'}   | ${undefined}
    ${'a literal claim'}      | ${'a/b/.github/workflows/deploy.yml@refs/heads/main'}
    ${'an unrelated pattern'} | ${'*/deploy.yml@*'}
  `('returns undefined for $description', ({ workflowRef }) => {
    // Given / When / Then
    expect(parseGithubWorkflowFilename(workflowRef)).toBeUndefined()
  })
})
