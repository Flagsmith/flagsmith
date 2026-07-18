import React, { FC, useEffect, useMemo, useState } from 'react'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
import Input from 'components/base/forms/Input'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import { getStore } from 'common/store'
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
import { createRoleMasterApiKey } from 'common/services/useRoleMasterApiKey'
import {
  deleteMasterAPIKeyWithMasterAPIKeyRoles,
  getRolesMasterAPIKeyWithMasterAPIKeyRoles,
} from 'common/services/useMasterAPIKeyWithMasterAPIKeyRole'
import TrustRelationshipPermissionsFields, {
  SelectedRole,
} from './TrustRelationshipPermissionsFields'
import WorkflowSetupSnippet, { GITHUB_ISSUER } from './WorkflowSetupSnippet'

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
  const [roles, setRoles] = useState<SelectedRole[]>([])

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

  useEffect(() => {
    if (trustRelationship) {
      getRolesMasterAPIKeyWithMasterAPIKeyRoles(getStore(), {
        org_id: organisationId,
        prefix: trustRelationship.master_api_key_prefix,
      }).then((res: { data?: { results: SelectedRole[] } }) => {
        setRoles(res.data?.results || [])
      })
    }
  }, [organisationId, trustRelationship])

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

  const addRole = (role: SelectedRole) => {
    if (isEdit) {
      createRoleMasterApiKey(getStore(), {
        body: { master_api_key: trustRelationship.master_api_key_id },
        org_id: organisationId,
        role_id: role.id,
      }).then(() => toast('Role assigned'))
    }
    setRoles((selected) => [...selected, { id: role.id, name: role.name }])
  }

  const removeRole = (roleId: number) => {
    if (isEdit) {
      deleteMasterAPIKeyWithMasterAPIKeyRoles(getStore(), {
        org_id: organisationId,
        prefix: trustRelationship.master_api_key_prefix,
        role_id: roleId,
      }).then(() => toast('Role removed'))
    }
    setRoles((selected) => selected.filter((role) => role.id !== roleId))
  }

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
        .then((created) =>
          Promise.all(
            roles.map((role) =>
              createRoleMasterApiKey(getStore(), {
                body: { master_api_key: created.master_api_key_id },
                org_id: organisationId,
                role_id: role.id,
              }),
            ),
          ),
        )
        .then(() => {
          toast('Trust relationship created')
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
          <label>Audience</label>
          <Input className='full-width' value={audience} readOnly />
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
            setRoles([])
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
