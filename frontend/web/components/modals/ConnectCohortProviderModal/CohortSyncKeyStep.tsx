import React, { FC, useState } from 'react'
import moment from 'moment'
import { Link } from 'react-router-dom'
import Constants from 'common/constants'
import { useHasPermission } from 'common/providers/Permission'
import {
  useCreateCohortSyncKeyMutation,
  useGetCohortSyncKeysQuery,
} from 'common/services/useCohort'
import { EnvironmentPermission } from 'common/types/permissions.types'
import { CohortSyncKey } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import InputGroup from 'components/base/forms/InputGroup'
import CopyField from 'components/CopyField'
import ErrorMessage from 'components/ErrorMessage'
import Tooltip from 'components/Tooltip'
import WarningMessage from 'components/WarningMessage'
import ConnectCohortProviderStep from './ConnectCohortProviderStep'

const NAME_MAX_LENGTH = 50

type CohortSyncKeyStepProps = {
  environmentApiKey: string
  index: number
  projectId: number | string
  providerLabel: string
}

const CohortSyncKeyStep: FC<CohortSyncKeyStepProps> = ({
  environmentApiKey,
  index,
  projectId,
  providerLabel,
}) => {
  const [name, setName] = useState('')
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [isCreateFormOpen, setIsCreateFormOpen] = useState(false)

  const { isLoading: isLoadingPermission, permission: canManage } =
    useHasPermission({
      id: environmentApiKey,
      level: 'environment',
      permission: EnvironmentPermission.MANAGE_SEGMENT_OVERRIDES,
    })

  const { data: syncKeys, isLoading } = useGetCohortSyncKeysQuery(
    { environmentApiKey },
    { skip: !environmentApiKey },
  )
  const [createCohortSyncKey, { error, isLoading: isCreating }] =
    useCreateCohortSyncKeyMutation()

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    createCohortSyncKey({ environmentApiKey, name: name.trim() })
      .unwrap()
      .then((syncKey) => {
        setCreatedKey(syncKey.key)
        setIsCreateFormOpen(false)
        setName('')
      })
      .catch(() => {})
  }

  const hasKeys = !!syncKeys?.length
  const getTitle = () => {
    if (createdKey) return 'Synchronisation key'
    if (hasKeys && !isCreateFormOpen) return 'Use your existing key'
    if (!canManage) return 'Synchronisation key'
    return 'Create a synchronisation key'
  }

  const renderBody = () => {
    if ((isLoading && !syncKeys) || isLoadingPermission) {
      return <Loader />
    }

    if (createdKey) {
      return (
        <>
          <CopyField
            value={createdKey}
            className='font-monospace'
            data-test='connect-provider-key-value'
          />
          <WarningMessage
            warningMessage='This key is shown only once. Store it securely — you will not be able to see it again.'
            warningMessageClass='mt-4'
          />
        </>
      )
    }

    if (!hasKeys && !canManage) {
      return (
        <div className='fs-small text-secondary'>
          You do not have permission to create synchronisation keys in this
          environment.
        </div>
      )
    }

    if (!hasKeys || isCreateFormOpen) {
      return (
        <form onSubmit={handleSubmit}>
          <InputGroup
            value={name}
            data-test='connect-provider-key-name'
            inputProps={{
              className: 'full-width',
              maxLength: NAME_MAX_LENGTH,
              name: 'name',
            }}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
              setName(event.target.value)
            }
            isValid={!!name.trim().length}
            type='text'
            placeholder={`e.g. ${providerLabel} production`}
          />
          <ErrorMessage error={error} />
          <Button
            type='submit'
            disabled={!name.trim() || isCreating}
            data-test='connect-provider-create-key'
          >
            {isCreating ? 'Creating' : 'Create Synchronisation Key'}
          </Button>
        </form>
      )
    }

    return (
      <>
        <div className='rounded border-1 d-flex flex-column'>
          {syncKeys?.map((syncKey: CohortSyncKey) => (
            <div
              key={syncKey.prefix}
              className='d-flex align-items-center justify-content-between gap-3 px-3 py-2'
            >
              <span className='fw-semibold'>{syncKey.name}</span>
              <span className='fs-small text-secondary d-flex align-items-center gap-3'>
                <span className='font-monospace'>{syncKey.prefix}</span>
                <span>{moment(syncKey.created).format('D MMM YYYY')}</span>
              </span>
            </div>
          ))}
        </div>
        <div className='fs-small text-secondary mt-2'>
          Key values are shown only at creation.
          {canManage && ' Lost it? Create a new key.'}
        </div>
        <div className='fs-small text-secondary'>
          You can revoke keys in{' '}
          <Link
            to={`/project/${projectId}/environment/${environmentApiKey}/settings?tab=cohort-synchronisation`}
            onClick={() => closeModal()}
          >
            Environment Settings
          </Link>
          .
        </div>
        {canManage ? (
          <Button
            theme='secondary'
            className='mt-3'
            onClick={() => setIsCreateFormOpen(true)}
            data-test='connect-provider-new-key'
          >
            Create a new key
          </Button>
        ) : (
          <Tooltip
            title={
              <Button theme='secondary' className='mt-3' disabled>
                Create a new key
              </Button>
            }
            place='right'
          >
            {Constants.environmentPermissions(
              EnvironmentPermission.MANAGE_SEGMENT_OVERRIDES,
            )}
          </Tooltip>
        )}
      </>
    )
  }

  return (
    <ConnectCohortProviderStep index={index} title={getTitle()}>
      {renderBody()}
    </ConnectCohortProviderStep>
  )
}

export default CohortSyncKeyStep
