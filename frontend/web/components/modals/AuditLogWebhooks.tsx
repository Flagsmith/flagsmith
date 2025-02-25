import React, { FC } from 'react'
import JSONReference from 'components/JSONReference'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import Constants from 'common/constants'
import {
  deleteAuditLogWebhook,
  useGetAuditLogWebhooksQuery,
} from 'common/services/useAuditLogWebhook'
import CreateAuditWebhookModal from './CreateAuditLogWebhook'
import AccountStore from 'common/stores/account-store'
import ConfirmRemoveAuditWebhook from './ConfirmRemoveAuditWebhook'
import { getStore } from 'common/store'
import { Webhook } from 'common/types/responses'
import Switch from 'components/Switch'
import moment from 'moment'
import Panel from 'components/base/grid/Panel'
import PanelSearch from 'components/PanelSearch'

type AuditLogWebhooksType = {
  organisationId: string
}

const AuditLogWebhooks: FC<AuditLogWebhooksType> = ({ organisationId }) => {
  const { data: webhooks, isLoading: webhooksLoading } =
    useGetAuditLogWebhooksQuery({ organisationId }, { skip: !organisationId })
  const createWebhook = () => {
    openModal(
      'New Webhook',
      <CreateAuditWebhookModal
        organisationId={AccountStore.getOrganisation().id}
      />,
      'side-modal',
    )
  }

  const editWebhook = (webhook: Webhook) => {
    openModal(
      'Edit Webhook',
      <CreateAuditWebhookModal
        webhook={webhook}
        organisationId={AccountStore.getOrganisation().id}
      />,
      'side-modal',
    )
  }

  const deleteWebhook = (webhook: Webhook) => {
    openModal(
      'Remove Webhook',
      <ConfirmRemoveAuditWebhook
        url={webhook.url}
        cb={() =>
          deleteAuditLogWebhook(getStore(), {
            id: webhook.id,
            organisationId: AccountStore.getOrganisation().id,
          })
        }
      />,
      'p-0',
    )
  }

  return (
    <>
      <JSONReference title={'Webhooks'} json={webhooks} />
      <div className='d-flex align-items-center'>
        <div className='flex-fill'>
          <h5 className='mb-2'>Audit Webhooks</h5>
          <p className='fs-small lh-sm mb-4'>
            Audit webhooks let you know when audit logs occur. You can configure
            1 or more audit webhooks per organisation.
            <br />
            <Button
              theme='text'
              href='https://docs.flagsmith.com/system-administration/webhooks'
              className='fw-normal'
            >
              Learn about Audit Webhooks.
            </Button>
          </p>
        </div>

        <Button onClick={createWebhook}>Create audit webhook</Button>
      </div>
      {webhooksLoading && !webhooks ? (
        <Loader />
      ) : (
        <PanelSearch
          id='webhook-list'
          className='no-pad'
          items={webhooks?.results}
          renderRow={(webhook: Webhook) => (
            <Row
              onClick={() => {
                editWebhook(webhook)
              }}
              space
              className='list-item clickable cursor-pointer'
              key={webhook.id}
            >
              <Flex className='table-column px-3'>
                <div className='font-weight-medium mb-1'>{webhook.url}</div>
                {webhook.created_at ? (
                  <div className='list-item-description'>
                    Created {moment(webhook.created_at).format('DD/MMM/YYYY')}
                  </div>
                ) : null}
              </Flex>
              <div className='table-column'>
                <Switch checked={webhook.enabled} />
              </div>
              <div className='table-column'>
                <Button
                  id='delete-invite'
                  type='button'
                  onClick={(e) => {
                    e.stopPropagation()
                    e.preventDefault()
                    deleteWebhook(webhook)
                  }}
                  className='btn btn-with-icon'
                >
                  <Icon name='trash-2' width={20} fill='#656D7B' />
                </Button>
              </div>
            </Row>
          )}
          renderNoResults={
            <Panel
              className='no-pad'
              title={
                <Tooltip
                  title={
                    <h5 className='mb-0'>
                      Webhooks <Icon name='info-outlined' />
                    </h5>
                  }
                  place='right'
                >
                  {Constants.strings.AUDIT_WEBHOOKS_DESCRIPTION}
                </Tooltip>
              }
            >
              <div className='search-list'>
                <Row className='list-item p-3 text-muted'>
                  You currently have no webhooks configured for this
                  organisation.
                </Row>
              </div>
            </Panel>
          }
          isLoading={webhooksLoading}
        />
      )}
    </>
  )
}

export default AuditLogWebhooks
