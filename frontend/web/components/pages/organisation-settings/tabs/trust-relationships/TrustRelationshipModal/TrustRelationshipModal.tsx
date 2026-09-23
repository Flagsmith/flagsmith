import React, { FC, useId, useMemo, useState } from 'react'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
import FieldLabel from 'components/base/forms/FieldLabel'
import Icon from 'components/icons/Icon'
import Input from 'components/base/forms/Input'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import { TrustRelationship } from 'common/types/responses'
import {
  useCreateTrustRelationshipMutation,
  useUpdateTrustRelationshipMutation,
} from 'common/services/useTrustRelationship'
import {
  trustRelationshipAlertError,
  trustRelationshipFieldErrors,
} from 'components/pages/organisation-settings/tabs/trust-relationships/errors'
import useTrustRelationshipRoles from 'components/pages/organisation-settings/tabs/trust-relationships/hooks/useTrustRelationshipRoles'
import TrustRelationshipPermissionsFields from 'components/pages/organisation-settings/tabs/trust-relationships/TrustRelationshipPermissionsFields'
import WorkflowSetupSnippet from 'components/pages/organisation-settings/tabs/trust-relationships/WorkflowSetupSnippet'
import { GITHUB_ISSUER } from 'components/pages/organisation-settings/tabs/trust-relationships/github'

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
  const claimRulesLabelId = useId()
  const valuesHintId = useId()
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
  const { addRole, assignRoles, clearRoles, removeRole, roles } =
    useTrustRelationshipRoles(organisationId, trustRelationship)

  const [
    createTrustRelationship,
    { error: createError, isLoading: isCreating },
  ] = useCreateTrustRelationshipMutation()
  const [
    updateTrustRelationship,
    { error: updateError, isLoading: isUpdating },
  ] = useUpdateTrustRelationshipMutation()
  const error = createError || updateError
  // Field-keyed errors render inline on their inputs; the alert carries
  // whatever has no field to attach to.
  const fieldErrors = useMemo(
    () => trustRelationshipFieldErrors(error),
    [error],
  )
  const alertError = useMemo(
    () =>
      trustRelationshipAlertError(error, 'Could not save trust relationship'),
    [error],
  )

  const onIsAdminChange = () => {
    // Turning admin on detaches any assigned roles server-side.
    if (!isAdmin) {
      clearRoles()
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

  return (
    <div className='p-4'>
      <InputGroup
        title='Name'
        inputProps={{ className: 'full-width', error: fieldErrors.name }}
        value={name}
        onChange={(e: InputEvent) => setName(Utils.safeParseEventValue(e))}
        placeholder='e.g. GitHub Actions'
      />
      <InputGroup
        title='Trusted issuer URL'
        inputProps={{ className: 'full-width', error: fieldErrors.issuer }}
        value={issuer}
        onChange={(e: InputEvent) => setIssuer(Utils.safeParseEventValue(e))}
        placeholder='e.g. https://token.actions.githubusercontent.com'
      />
      <InputGroup
        title='Expected audience'
        inputProps={{ className: 'full-width', error: fieldErrors.audience }}
        value={audience}
        onChange={(e: InputEvent) => setAudience(Utils.safeParseEventValue(e))}
        placeholder='e.g. https://github.com/YourOrg'
      />
      <FieldLabel id={claimRulesLabelId}>Claim matching rules</FieldLabel>
      <div role='group' aria-labelledby={claimRulesLabelId}>
        {claimRules.map((rule, index) => (
          <Row key={index} className='mb-2 gap-2'>
            <Flex>
              <Input
                aria-label={`Claim for rule ${index + 1}`}
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
                aria-label={`Values for rule ${index + 1}`}
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
                aria-describedby={valuesHintId}
              />
            </Flex>
            <Button
              className='btn btn-with-icon'
              onClick={() =>
                setClaimRules((rules) => rules.filter((_, i) => i !== index))
              }
              aria-label={`Remove rule ${index + 1}`}
            >
              <Icon name='trash-2' width={20} />
            </Button>
          </Row>
        ))}
      </div>
      <div id={valuesHintId} className='text-muted mb-2'>
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
              .find((rule) => rule.claim.trim() === 'environment')
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
          disabled={!name || !issuer || !audience}
          isLoading={isCreating || isUpdating}
        >
          {isEdit ? 'Save trust relationship' : 'Create trust relationship'}
        </Button>
      </div>
    </div>
  )
}

export default TrustRelationshipModal
