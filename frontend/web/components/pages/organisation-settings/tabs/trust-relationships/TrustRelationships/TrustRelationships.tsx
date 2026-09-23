import React, { FC } from 'react'
import moment from 'moment'
import Button from 'components/base/forms/Button'
import EmptyState from 'components/EmptyState'
import Icon from 'components/icons/Icon'
import PageTitle from 'components/PageTitle'
import PanelSearch from 'components/PanelSearch'
import Switch from 'components/Switch'
import GithubTrustRelationshipForm from 'components/pages/organisation-settings/tabs/trust-relationships/GithubTrustRelationshipForm'
import { trustRelationshipErrorMessage } from 'components/pages/organisation-settings/tabs/trust-relationships/errors'
import NewTrustRelationshipModal from 'components/pages/organisation-settings/tabs/trust-relationships/NewTrustRelationshipModal'
import TrustRelationshipModal from 'components/pages/organisation-settings/tabs/trust-relationships/TrustRelationshipModal'
import { isGithubFormEditable } from 'components/pages/organisation-settings/tabs/trust-relationships/github'
import { providerIconForIssuer } from 'components/pages/organisation-settings/tabs/trust-relationships/providers'
import { TrustRelationship } from 'common/types/responses'
import {
  useDeleteTrustRelationshipMutation,
  useGetTrustRelationshipsQuery,
} from 'common/services/useTrustRelationship'
import './TrustRelationships.scss'

// Header and body cells share these, so a column cannot drift out of alignment.
const COLUMN = {
  config: 'trust-relationships__config-column table-column',
  name: 'trust-relationships__name-column table-column px-3',
  narrow: 'trust-relationships__narrow-column table-column',
}

const NameCell: FC<{ trustRelationship: TrustRelationship }> = ({
  trustRelationship,
}) => (
  <Row className='gap-2 align-items-center' noWrap>
    <span
      className='d-flex align-items-center justify-content-center flex-shrink-0 p-2 rounded-lg bg-surface-muted'
      aria-hidden
    >
      {providerIconForIssuer(trustRelationship.issuer, 20)}
    </span>
    <div className='trust-relationships__name-body'>
      <div className='font-weight-medium text-break'>
        {trustRelationship.name}
      </div>
      <div className='list-item-subtitle'>
        Created {moment(trustRelationship.created_at).format('Do MMM YYYY')}
      </div>
    </div>
  </Row>
)

// Both URLs read in full, labelled, so one column carries the whole exchange.
const ConfigurationCell: FC<{ trustRelationship: TrustRelationship }> = ({
  trustRelationship,
}) => (
  <dl className='trust-relationships__config m-0'>
    <dt className='font-weight-medium fs-captionSmall text-secondary text-uppercase m-0'>
      Issuer
    </dt>
    <dd className='font-monospace text-break m-0'>
      {trustRelationship.issuer}
    </dd>
    <dt className='font-weight-medium fs-captionSmall text-secondary text-uppercase m-0'>
      Audience
    </dt>
    <dd className='font-monospace text-break m-0'>
      {trustRelationship.audience}
    </dd>
  </dl>
)

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
              <div className={COLUMN.name}>Name</div>
              <div className={COLUMN.config}>OIDC configuration</div>
              <div className={COLUMN.narrow}>Is admin</div>
              <div className={COLUMN.narrow}>Remove</div>
            </Row>
          }
          renderRow={(trustRelationship: TrustRelationship) => (
            <Row
              className='list-item clickable'
              key={trustRelationship.id}
              onClick={() => editTrustRelationship(trustRelationship)}
              data-test={`trust-relationship-${trustRelationship.id}`}
            >
              <div className={COLUMN.name}>
                <NameCell trustRelationship={trustRelationship} />
              </div>
              <div className={COLUMN.config}>
                <ConfigurationCell trustRelationship={trustRelationship} />
              </div>
              <div
                className={COLUMN.narrow}
                onClick={(e) => e.stopPropagation()}
              >
                <Switch checked={trustRelationship.is_admin} disabled />
              </div>
              <div className={COLUMN.narrow}>
                <Button
                  className='btn btn-with-icon'
                  onClick={(e) => {
                    e.stopPropagation()
                    remove(trustRelationship)
                  }}
                  aria-label={`Delete ${trustRelationship.name}`}
                >
                  <Icon name='trash-2' width={20} />
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
