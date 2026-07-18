import React, { FC } from 'react'
import moment from 'moment'
import Button from 'components/base/forms/Button'
import EmptyState from 'components/EmptyState'
import Icon from 'components/icons/Icon'
import PageTitle from 'components/PageTitle'
import PanelSearch from 'components/PanelSearch'
import Switch from 'components/Switch'
import GithubTrustRelationshipForm from './GithubTrustRelationshipForm'
import { trustRelationshipErrorMessage } from './errors'
import NewTrustRelationshipModal from './NewTrustRelationshipModal'
import TrustRelationshipModal from './TrustRelationshipModal'
import { isGithubFormEditable } from './WorkflowSetupSnippet'
import { providerForIssuer } from './providers'
import { TrustRelationship } from 'common/types/responses'
import {
  useDeleteTrustRelationshipMutation,
  useGetTrustRelationshipsQuery,
} from 'common/services/useTrustRelationship'

const IssuerCell: FC<{ issuer: string }> = ({ issuer }) => {
  const provider = providerForIssuer(issuer)
  if (!provider) {
    return <span className='font-monospace'>{issuer}</span>
  }
  return (
    <Tooltip title={<span aria-label={provider.label}>{provider.icon}</span>}>
      {`<span class="font-monospace">${issuer}</span>`}
    </Tooltip>
  )
}

type TrustRelationshipsProps = {
  organisationId: number
}

const TrustRelationships: FC<TrustRelationshipsProps> = ({
  organisationId,
}) => {
  const { data, isLoading } = useGetTrustRelationshipsQuery(
    { organisation_id: organisationId },
    { skip: !organisationId },
  )
  const [deleteTrustRelationship] = useDeleteTrustRelationshipMutation()

  const editTrustRelationship = (trustRelationship: TrustRelationship) =>
    openModal(
      `${trustRelationship.name} trust relationship`,
      isGithubFormEditable(trustRelationship) ? (
        <GithubTrustRelationshipForm
          organisationId={organisationId}
          trustRelationship={trustRelationship}
          existingAudiences={(data?.results || []).map(
            (existing) => existing.audience,
          )}
        />
      ) : (
        <TrustRelationshipModal
          organisationId={organisationId}
          trustRelationship={trustRelationship}
        />
      ),
      'p-0 side-modal',
    )

  const addTrustRelationship = () =>
    openModal(
      'New trust relationship',
      <NewTrustRelationshipModal
        organisationId={organisationId}
        existingAudiences={(data?.results || []).map(
          (trustRelationship) => trustRelationship.audience,
        )}
      />,
      'p-0 side-modal',
    )

  const remove = (trustRelationship: TrustRelationship) => {
    openConfirm({
      body: (
        <div>
          Deleting the <strong>{trustRelationship.name}</strong> trust
          relationship immediately stops token exchange for it, and any
          outstanding access tokens stop working.
        </div>
      ),
      destructive: true,
      onYes: () => {
        deleteTrustRelationship({
          id: trustRelationship.id,
          organisation_id: organisationId,
        })
          .unwrap()
          .then(() => toast('Trust relationship deleted'))
          .catch((error) =>
            toast(
              trustRelationshipErrorMessage(
                error,
                'Could not delete trust relationship',
              ),
              'danger',
            ),
          )
      },
      title: 'Delete trust relationship',
      yesText: 'Delete',
    })
  }

  return (
    <div className='mt-4'>
      <PageTitle
        title='Trust relationships'
        cta={
          <Button onClick={addTrustRelationship}>Add trust relationship</Button>
        }
      >
        Let a trusted OIDC identity provider exchange its tokens for short-lived
        Flagsmith access tokens.
      </PageTitle>
      {!isLoading && !data?.results?.length && (
        <EmptyState
          icon='shield'
          title='No trust relationships'
          description='Add a trust relationship to let your CI authenticate with OIDC.'
        />
      )}
      {!!data?.results?.length && (
        <PanelSearch
          id='trust-relationships-list'
          items={data.results}
          header={
            <Row className='table-header'>
              <Flex className='table-column px-3'>Name</Flex>
              <Flex className='table-column'>Issuer</Flex>
              <Flex className='table-column'>Audience</Flex>
              <div className='table-column' style={{ width: 80 }}>
                Is admin
              </div>
              <div className='table-column' style={{ width: 80 }}>
                Remove
              </div>
            </Row>
          }
          renderRow={(trustRelationship: TrustRelationship) => (
            <Row
              className='list-item clickable'
              key={trustRelationship.id}
              onClick={() => editTrustRelationship(trustRelationship)}
              data-test={`trust-relationship-${trustRelationship.id}`}
            >
              <Flex className='table-column px-3'>
                <div className='font-weight-medium'>
                  {trustRelationship.name}
                </div>
                <div className='list-item-subtitle'>
                  Created{' '}
                  {moment(trustRelationship.created_at).format('Do MMM YYYY')}
                </div>
              </Flex>
              <Flex className='table-column'>
                <IssuerCell issuer={trustRelationship.issuer} />
              </Flex>
              <Flex className='table-column font-monospace'>
                {trustRelationship.audience}
              </Flex>
              <div
                className='table-column'
                style={{ width: 80 }}
                onClick={(e) => e.stopPropagation()}
              >
                <Switch checked={trustRelationship.is_admin} disabled />
              </div>
              <div className='table-column' style={{ width: 80 }}>
                <Button
                  theme='text'
                  onClick={(e) => {
                    e.stopPropagation()
                    remove(trustRelationship)
                  }}
                  data-test={`remove-trust-relationship-${trustRelationship.id}`}
                >
                  <Icon name='trash-2' width={20} fill='#656D7B' />
                </Button>
              </div>
            </Row>
          )}
        />
      )}
    </div>
  )
}

export default TrustRelationships
