import React, { FC } from 'react'
import moment from 'moment'

import Button from './base/forms/Button'
import EmptyState from './EmptyState'
import Icon from './icons/Icon'
import Loader from './Loader'
import PageTitle from './PageTitle'
import ScimTokenModal from './modals/ScimTokenModal'
import Utils from 'common/utils/utils'
import {
  useCreateScimConfigurationMutation,
  useDeleteScimConfigurationMutation,
  useGetScimConfigurationQuery,
  useRegenerateScimTokenMutation,
} from 'common/services/useScimConfiguration'

type ScimSectionProps = {
  organisationId: number
}

const DATE_FORMAT = 'Do MMM YYYY HH:mma'

const ScimSection: FC<ScimSectionProps> = ({ organisationId }) => {
  const { data, error, isLoading } = useGetScimConfigurationQuery({
    organisation_id: organisationId,
  })
  const [createScimConfiguration, { isLoading: isCreating }] =
    useCreateScimConfigurationMutation()
  const [regenerateScimToken, { isLoading: isRegenerating }] =
    useRegenerateScimTokenMutation()
  const [deleteScimConfiguration, { isLoading: isDeleting }] =
    useDeleteScimConfigurationMutation()

  const showTokenModal = (token: string) => {
    openModal('Save your SCIM bearer token', <ScimTokenModal token={token} />)
  }

  const onCreate = () => {
    createScimConfiguration({ organisation_id: organisationId })
      .unwrap()
      .then((result) => {
        showTokenModal(result.token)
        toast('SCIM configuration created')
      })
      .catch(() => {
        toast('Could not create SCIM configuration', 'danger')
      })
  }

  const onRegenerate = () => {
    openConfirm({
      body: (
        <div>
          Regenerating will invalidate the existing token. Any identity provider
          currently using it will stop syncing until the new token is
          configured.
        </div>
      ),
      destructive: true,
      onYes: () => {
        regenerateScimToken({ organisation_id: organisationId })
          .unwrap()
          .then((result) => {
            showTokenModal(result.token)
            toast('SCIM token regenerated')
          })
          .catch(() => {
            toast('Could not regenerate SCIM token', 'danger')
          })
      },
      title: 'Regenerate SCIM token',
      yesText: 'Regenerate',
    })
  }

  const onDelete = () => {
    openConfirm({
      body: (
        <div>
          Deleting the SCIM configuration will stop automatic user provisioning.
          Existing users and groups are not affected.
        </div>
      ),
      destructive: true,
      onYes: () => {
        deleteScimConfiguration({ organisation_id: organisationId })
          .unwrap()
          .then(() => {
            toast('SCIM configuration deleted')
          })
          .catch(() => {
            toast('Could not delete SCIM configuration', 'danger')
          })
      },
      title: 'Delete SCIM configuration',
      yesText: 'Delete',
    })
  }

  const onCopyBaseUrl = () => {
    if (data?.base_url) {
      Utils.copyToClipboard(data.base_url)
    }
  }

  if (isLoading) {
    return (
      <div className='mt-4 mb-4'>
        <PageTitle title='SCIM Configuration' />
        <div className='py-4 text-center'>
          <Loader />
        </div>
      </div>
    )
  }

  // RTK Query surfaces HTTP errors via `error.status`. 404 = no configuration
  // exists for this organisation, which is our empty state. Don't gate on
  // `!data` — after a successful fetch followed by a delete, RTK keeps stale
  // `data` alongside the new 404 error; trusting the error alone reflects
  // the server state correctly.
  const isNotFound =
    !!error &&
    typeof error === 'object' &&
    'status' in error &&
    error.status === 404

  if (isNotFound) {
    return (
      <div className='mt-4 mb-4'>
        <PageTitle title='SCIM Configuration' />
        <EmptyState
          icon='people'
          title='No SCIM configuration'
          description='Automatically provision and de-provision users and groups from your identity provider via SCIM 2.0.'
          action={
            <Button
              onClick={onCreate}
              disabled={isCreating}
              data-test='scim-create'
            >
              {isCreating ? 'Creating…' : 'Create SCIM configuration'}
            </Button>
          }
        />
      </div>
    )
  }

  if (!data) {
    return null
  }

  return (
    <div className='mt-4 mb-4'>
      <PageTitle title='SCIM Configuration' />
      <Row className='gap-4 mb-3'>
        <div>
          <div className='text-muted text-uppercase fs-caption'>Created</div>
          <div className='font-weight-medium'>
            {moment(data.created_at).format(DATE_FORMAT)}
          </div>
        </div>
        <div>
          <div className='text-muted text-uppercase fs-caption'>
            Token last rotated
          </div>
          <div className='font-weight-medium'>
            {moment(data.token_rotated_at).format(DATE_FORMAT)}
          </div>
        </div>
      </Row>

      <div className='mb-3'>
        <div className='text-muted text-uppercase fs-caption mb-1'>
          SCIM base URL
        </div>
        <Row className='gap-2 align-items-center'>
          <Flex>
            <Input
              value={data.base_url}
              inputProps={{ readOnly: true }}
              data-test='scim-base-url'
            />
          </Flex>
          <Button theme='secondary' onClick={onCopyBaseUrl}>
            Copy
          </Button>
        </Row>
      </div>

      <Row className='gap-2'>
        <Button
          theme='secondary'
          onClick={onRegenerate}
          disabled={isRegenerating}
          data-test='scim-regenerate'
        >
          {isRegenerating ? 'Regenerating…' : 'Regenerate Token'}
        </Button>
        <Button
          theme='danger'
          onClick={onDelete}
          disabled={isDeleting}
          data-test='scim-delete'
        >
          <Icon name='trash-2' width={16} fill='#fff' />
          <span className='ms-1'>Delete</span>
        </Button>
      </Row>
    </div>
  )
}

ScimSection.displayName = 'ScimSection'

export default ScimSection
