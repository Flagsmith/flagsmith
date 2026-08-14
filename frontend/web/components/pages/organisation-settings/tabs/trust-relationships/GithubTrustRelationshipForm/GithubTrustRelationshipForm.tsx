import React, { FC, useEffect, useMemo, useState } from 'react'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
import Input from 'components/base/forms/Input'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import {
  Repository,
  TrustRelationship,
  TrustRelationshipClaimRule,
} from 'common/types/responses'
import { useGetGithubIntegrationQuery } from 'common/services/useGithubIntegration'
import { useGetGithubReposQuery } from 'common/services/useGithub'
import {
  useCreateTrustRelationshipMutation,
  useUpdateTrustRelationshipMutation,
} from 'common/services/useTrustRelationship'
import useTrustRelationshipRoles from 'components/pages/organisation-settings/tabs/trust-relationships/hooks/useTrustRelationshipRoles'
import TrustRelationshipPermissionsFields from 'components/pages/organisation-settings/tabs/trust-relationships/TrustRelationshipPermissionsFields'
import WorkflowSetupSnippet, {
  GITHUB_ISSUER,
} from 'components/pages/organisation-settings/tabs/trust-relationships/WorkflowSetupSnippet'

type GithubTrustRelationshipFormProps = {
  organisationId: number
  existingAudiences: string[]
  trustRelationship?: TrustRelationship
}

const ruleValue = (
  trustRelationship: TrustRelationship | undefined,
  claim: string,
): string | undefined =>
  trustRelationship?.claim_rules.find((rule) => rule.claim === claim)?.values[0]

const GithubTrustRelationshipForm: FC<GithubTrustRelationshipFormProps> = ({
  existingAudiences,
  organisationId,
  trustRelationship,
}) => {
  const isEdit = !!trustRelationship
  const { data: githubIntegrations } = useGetGithubIntegrationQuery({
    organisation_id: organisationId,
  })
  const installationId = githubIntegrations?.results?.[0]?.installation_id
  const { data: repos } = useGetGithubReposQuery(
    { installation_id: installationId || '', organisation_id: organisationId },
    { skip: !installationId },
  )

  const initialRepoFullName = ruleValue(trustRelationship, 'repository') || ''
  const pinnedRepoId = ruleValue(trustRelationship, 'repository_id')

  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null)
  const [manualOwner, setManualOwner] = useState(
    initialRepoFullName.split('/')[0] || '',
  )
  const [manualRepo, setManualRepo] = useState(
    initialRepoFullName.split('/')[1] || '',
  )
  const [environment, setEnvironment] = useState(
    ruleValue(trustRelationship, 'environment') || '',
  )
  const [isAdmin, setIsAdmin] = useState(trustRelationship?.is_admin ?? true)
  const { addRole, assignRoles, clearRoles, removeRole, roles } =
    useTrustRelationshipRoles(organisationId, trustRelationship)

  // A repository pinned by ID resolves through the installation's repo list.
  const pinnedRepo = useMemo(
    () =>
      pinnedRepoId
        ? repos?.results?.find((repo) => `${repo.id}` === pinnedRepoId)
        : undefined,
    [pinnedRepoId, repos],
  )
  useEffect(() => {
    if (pinnedRepo && !selectedRepo) {
      setSelectedRepo(pinnedRepo)
    }
  }, [pinnedRepo, selectedRepo])

  const [
    createTrustRelationship,
    { error: createError, isLoading: isCreating },
  ] = useCreateTrustRelationshipMutation()
  const [
    updateTrustRelationship,
    { error: updateError, isLoading: isUpdating },
  ] = useUpdateTrustRelationshipMutation()

  const isUnresolvedPin = !!pinnedRepoId && !pinnedRepo
  const owner = selectedRepo?.owner?.login || manualOwner.trim()
  const manualFullName =
    manualOwner.trim() && manualRepo.trim()
      ? `${manualOwner.trim()}/${manualRepo.trim()}`
      : ''
  const repoFullName = selectedRepo ? selectedRepo.full_name : manualFullName
  const repoChanged =
    !isEdit || (!isUnresolvedPin && repoFullName !== initialRepoFullName)

  // GitHub's default `aud` is the repository owner's URL, so the first trust
  // relationship per owner needs no audience configuration in the workflow.
  const audience = useMemo(() => {
    if (isEdit && !repoChanged) return trustRelationship.audience
    if (!owner) return ''
    const otherAudiences = existingAudiences.filter(
      (existing) => existing !== trustRelationship?.audience,
    )
    const ownerAudience = `https://github.com/${owner}`
    return otherAudiences.includes(ownerAudience)
      ? `https://github.com/${repoFullName}`
      : ownerAudience
  }, [
    isEdit,
    repoChanged,
    trustRelationship,
    owner,
    repoFullName,
    existingAudiences,
  ])

  const save = () => {
    const claimRules: TrustRelationshipClaimRule[] = []
    if (isUnresolvedPin) {
      claimRules.push({ claim: 'repository_id', values: [pinnedRepoId] })
    } else if (selectedRepo) {
      // The numeric repository id survives renames; names are reclaimable.
      claimRules.push({
        claim: 'repository_id',
        values: [`${selectedRepo.id}`],
      })
    } else {
      claimRules.push({ claim: 'repository', values: [repoFullName] })
    }
    if (environment.trim()) {
      claimRules.push({ claim: 'environment', values: [environment.trim()] })
    }
    const body = {
      audience,
      claim_rules: claimRules,
      is_admin: isAdmin,
      issuer: GITHUB_ISSUER,
      name:
        isUnresolvedPin && trustRelationship
          ? trustRelationship.name
          : `GitHub Actions (${repoFullName})`,
    }
    if (isEdit) {
      updateTrustRelationship({
        body,
        id: trustRelationship.id,
        organisation_id: organisationId,
      })
        .unwrap()
        .then(() => {
          toast('Trust relationship updated')
          closeModal()
        })
        .catch(() => null)
    } else {
      createTrustRelationship({ body, organisation_id: organisationId })
        .unwrap()
        .then((created) => assignRoles(created.master_api_key_id))
        .then((allAssigned) => {
          if (allAssigned) {
            toast('Trust relationship created')
          } else {
            toast(
              'Trust relationship created, but some roles could not be assigned',
              'danger',
            )
          }
          closeModal()
        })
        .catch(() => null)
    }
  }

  let repositoryFields = (
    <>
      <InputGroup
        title='Repository owner'
        inputProps={{ className: 'full-width' }}
        value={manualOwner}
        onChange={(e: InputEvent) =>
          setManualOwner(Utils.safeParseEventValue(e))
        }
        placeholder='e.g. YourOrg'
      />
      <InputGroup
        title='Repository name'
        inputProps={{ className: 'full-width' }}
        value={manualRepo}
        onChange={(e: InputEvent) =>
          setManualRepo(Utils.safeParseEventValue(e))
        }
        placeholder='e.g. your-repo'
      />
      <div className='text-muted mb-3'>
        Install the{' '}
        <Button
          theme='text'
          className='fw-normal'
          href={`/organisation/${organisationId}/integrations`}
          target='_blank'
        >
          Flagsmith GitHub integration
        </Button>{' '}
        to pick repositories from a list.
      </div>
    </>
  )
  if (isUnresolvedPin) {
    repositoryFields = (
      <InputGroup
        title='Repository'
        component={
          <Input
            className='full-width'
            value={`Pinned by repository ID ${pinnedRepoId}`}
            readOnly
          />
        }
      />
    )
  } else if (installationId) {
    repositoryFields = (
      <InputGroup
        title='Repository'
        component={
          <Select
            value={
              selectedRepo
                ? {
                    label: selectedRepo.full_name,
                    value: selectedRepo.full_name,
                  }
                : null
            }
            placeholder='Select a repository'
            options={(repos?.results || []).map((repo) => ({
              label: repo.full_name,
              repo,
              value: repo.full_name,
            }))}
            onChange={(option: { repo: Repository }) =>
              setSelectedRepo(option.repo)
            }
          />
        }
      />
    )
  }

  return (
    <div className='p-4'>
      {repositoryFields}
      <InputGroup
        title='GitHub environment (optional)'
        inputProps={{ className: 'full-width' }}
        value={environment}
        onChange={(e: InputEvent) =>
          setEnvironment(Utils.safeParseEventValue(e))
        }
        placeholder='e.g. production'
      />
      {!!audience && (
        <>
          <InputGroup
            title='Audience'
            component={
              <Input className='full-width' value={audience} readOnly />
            }
          />
          <WorkflowSetupSnippet
            audience={audience}
            environment={environment.trim() || undefined}
          />
        </>
      )}
      <TrustRelationshipPermissionsFields
        organisationId={organisationId}
        isAdmin={isAdmin}
        onIsAdminChange={() => {
          if (!isAdmin) {
            clearRoles()
          }
          setIsAdmin(!isAdmin)
        }}
        roles={roles}
        onAddRole={addRole}
        onRemoveRole={removeRole}
      />
      <ErrorMessage error={createError || updateError} />
      <div className='text-right mt-4'>
        <Button
          onClick={save}
          disabled={
            (!repoFullName && !isUnresolvedPin) || isCreating || isUpdating
          }
        >
          {isEdit ? 'Save trust relationship' : 'Create trust relationship'}
        </Button>
      </div>
    </div>
  )
}

export default GithubTrustRelationshipForm
