import React, { FC, useEffect, useMemo, useState } from 'react'
import { IonIcon } from '@ionic/react'
import { close as closeIcon } from 'ionicons/icons'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
import Input from 'components/base/forms/Input'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import { getStore } from 'common/store'
import { TrustRelationship } from 'common/types/responses'
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

type ClaimRuleRow = { claim: string; values: string }

type TrustRelationshipModalProps = {
  organisationId: number
  trustRelationship?: TrustRelationship
}

const TrustRelationshipModal: FC<TrustRelationshipModalProps> = ({
  organisationId,
  trustRelationship,
}) => {
  const isEdit = !!trustRelationship
  const [name, setName] = useState(trustRelationship?.name || '')
  const [issuer, setIssuer] = useState(trustRelationship?.issuer || '')
  const [audience, setAudience] = useState(trustRelationship?.audience || '')
  const [claimRules, setClaimRules] = useState<ClaimRuleRow[]>(
    trustRelationship?.claim_rules.map((rule) => ({
      claim: rule.claim,
      values: rule.values.join(', '),
    })) || [],
  )
  const [isAdmin, setIsAdmin] = useState(trustRelationship?.is_admin ?? true)
  const [roles, setRoles] = useState<SelectedRole[]>([])

  const [
    createTrustRelationship,
    { error: createError, isLoading: isCreating },
  ] = useCreateTrustRelationshipMutation()
  const [
    updateTrustRelationship,
    { error: updateError, isLoading: isUpdating },
  ] = useUpdateTrustRelationshipMutation()
  const fieldErrors = ((createError || updateError) as { data?: any })?.data
  // Field-keyed errors render inline on their inputs; the alert carries
  // whatever has no field to attach to.
  const alertError = useMemo(() => {
    const error = (createError || updateError) as { data?: any } | undefined
    const data = error?.data
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      const rest = Object.fromEntries(
        Object.entries(data).filter(
          ([key]) => !['audience', 'issuer', 'name'].includes(key),
        ),
      )
      return Object.keys(rest).length ? { ...error, data: rest } : null
    }
    return error
  }, [createError, updateError])

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

  const onIsAdminChange = () => {
    // Turning admin on detaches any assigned roles server-side.
    if (!isAdmin) {
      setRoles([])
    }
    setIsAdmin(!isAdmin)
  }

  const body = {
    audience,
    claim_rules: claimRules
      .filter((rule) => rule.claim)
      .map((rule) => ({
        claim: rule.claim.trim(),
        values: rule.values
          .split(',')
          .map((value) => value.trim())
          .filter(Boolean),
      })),
    is_admin: isAdmin,
    issuer,
    name,
  }

  const save = () => {
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
      createTrustRelationship({
        body,
        organisation_id: organisationId,
      })
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

  return (
    <div className='p-4'>
      <InputGroup
        title='Name'
        inputProps={{ className: 'full-width', error: fieldErrors?.name }}
        value={name}
        onChange={(e: InputEvent) => setName(Utils.safeParseEventValue(e))}
        placeholder='e.g. GitHub Actions'
      />
      <InputGroup
        title='Trusted issuer URL'
        inputProps={{ className: 'full-width', error: fieldErrors?.issuer }}
        value={issuer}
        onChange={(e: InputEvent) => setIssuer(Utils.safeParseEventValue(e))}
        placeholder='e.g. https://token.actions.githubusercontent.com'
      />
      <InputGroup
        title='Expected audience'
        inputProps={{ className: 'full-width', error: fieldErrors?.audience }}
        value={audience}
        onChange={(e: InputEvent) => setAudience(Utils.safeParseEventValue(e))}
        placeholder='e.g. https://github.com/YourOrg'
      />
      <label>Claim matching rules</label>
      {claimRules.map((rule, index) => (
        <Row key={index} className='mb-2 gap-2'>
          <Flex>
            <Input
              value={rule.claim}
              className='full-width'
              onChange={(e: InputEvent) =>
                setClaimRules((rules) =>
                  rules.map((r, i) =>
                    i === index
                      ? { ...r, claim: Utils.safeParseEventValue(e) }
                      : r,
                  ),
                )
              }
              placeholder='Claim, e.g. repository'
            />
          </Flex>
          <Flex>
            <Input
              value={rule.values}
              className='full-width'
              onChange={(e: InputEvent) =>
                setClaimRules((rules) =>
                  rules.map((r, i) =>
                    i === index
                      ? { ...r, values: Utils.safeParseEventValue(e) }
                      : r,
                  ),
                )
              }
              placeholder='Values, e.g. YourOrg/your-repo'
            />
          </Flex>
          <Button
            theme='text'
            onClick={() =>
              setClaimRules((rules) => rules.filter((_, i) => i !== index))
            }
          >
            <IonIcon icon={closeIcon} />
          </Button>
        </Row>
      ))}
      <div className='text-muted mb-2'>
        Values support * wildcards; separate alternatives with commas.
      </div>
      <Button
        theme='outline'
        onClick={() =>
          setClaimRules((rules) => [...rules, { claim: '', values: '' }])
        }
      >
        Add rule
      </Button>
      {issuer.trim().replace(/\/+$/, '') === GITHUB_ISSUER && !!audience && (
        <WorkflowSetupSnippet
          audience={audience}
          environment={
            claimRules
              .find((rule) => rule.claim === 'environment')
              ?.values.split(',')[0]
              ?.trim() || undefined
          }
        />
      )}
      <TrustRelationshipPermissionsFields
        organisationId={organisationId}
        isAdmin={isAdmin}
        onIsAdminChange={onIsAdminChange}
        roles={roles}
        onAddRole={addRole}
        onRemoveRole={removeRole}
      />
      <ErrorMessage error={alertError} />
      <div className='text-right mt-4'>
        <Button
          onClick={save}
          disabled={!name || !issuer || !audience || isCreating || isUpdating}
        >
          {isEdit ? 'Save trust relationship' : 'Create trust relationship'}
        </Button>
      </div>
    </div>
  )
}

export default TrustRelationshipModal
