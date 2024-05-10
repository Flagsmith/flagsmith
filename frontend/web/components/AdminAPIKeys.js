import React, { PureComponent } from 'react'
import { close as closeIcon } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'
import data from 'common/data/base/_data'
import InfoMessage from './InfoMessage'
import Token from './Token'
import JSONReference from './JSONReference'
import Button from './base/forms/Button'
import DateSelect from './DateSelect'
import Icon from './Icon'
import Switch from './Switch'
import MyRoleSelect from './MyRoleSelect'
import { getStore } from 'common/store'
import { createRoleMasterApiKey } from 'common/services/useRoleMasterApiKey'
import {
  deleteMasterAPIKeyWithMasterAPIKeyRoles,
  getMasterAPIKeyWithMasterAPIKeyRoles,
  getRolesMasterAPIKeyWithMasterAPIKeyRoles,
  updateMasterAPIKeyWithMasterAPIKeyRoles,
} from 'common/services/useMasterAPIKeyWithMasterAPIKeyRole'

export class CreateAPIKey extends PureComponent {
  state = {
    expiry_date: null,
    is_admin: true,
    key: '',
    name: '',
    roles: [],
    showRoles: false,
  }

  componentDidMount() {
    this.props.isEdit && this.getApiKeyByPrefix(this.props.prefix)
  }

  submit = () => {
    this.setState({ isSaving: true })
    data
      .post(
        `${Project.api}organisations/${this.props.organisationId}/master-api-keys/`,
        {
          expiry_date: this.state.expiry_date,
          is_admin: this.state.is_admin,
          name: this.state.name,
          organisation: this.props.organisationId,
        },
      )
      .then((res) => {
        this.setState({
          isSaving: false,
          key: res.key,
        })
        Promise.all(
          this.state.roles.map((role) =>
            createRoleMasterApiKey(getStore(), {
              body: { master_api_key: res.id },
              org_id: AccountStore.getOrganisation().id,
              role_id: role.id,
            }).then(() => {
              toast('Role API Key was Created')
            }),
          ),
        )

        this.props.onSuccess()
      })
  }

  updateApiKey = (prefix) => {
    updateMasterAPIKeyWithMasterAPIKeyRoles(getStore(), {
      body: {
        expiry_date: this.state.expiry_date,
        is_admin: this.state.is_admin,
        name: this.state.name,
        revoked: false,
      },
      org_id: AccountStore.getOrganisation().id,
      prefix: prefix,
    }).then(() => {
      this.props.onSuccess()
    })
  }

  getApiKeyByPrefix = (prefix) => {
    getMasterAPIKeyWithMasterAPIKeyRoles(getStore(), {
      org_id: AccountStore.getOrganisation().id,
      prefix: prefix,
    }).then((res) => {
      this.setState({
        expiry_date: res.data.expiry_date,
        is_admin: res.data.is_admin,
        name: res.data.name,
      })
      getRolesMasterAPIKeyWithMasterAPIKeyRoles(getStore(), {
        org_id: AccountStore.getOrganisation().id,
        prefix: prefix,
      }).then((rolesData) => {
        this.setState({
          roles: rolesData.data.results,
        })
      })
    })
  }

  removeRoleApiKey = (roleId, isEdit) => {
    const roleSelected = this.state.roles.find((item) => item.id === roleId)
    if (isEdit) {
      deleteMasterAPIKeyWithMasterAPIKeyRoles(getStore(), {
        org_id: AccountStore.getOrganisation().id,
        prefix: this.props.prefix,
        role_id: roleSelected.id,
      }).then(() => {
        toast('Role API Key was removed')
      })
    }
    this.setState({
      roles: (this.state.roles || []).filter((v) => v.id !== roleId),
    })
  }

  addRole = (role, isEdit) => {
    if (isEdit) {
      createRoleMasterApiKey(getStore(), {
        body: { master_api_key: this.props.masterAPIKey },
        org_id: AccountStore.getOrganisation().id,
        role_id: role.id,
      }).then((res) => {
        toast('Role API Key was added')
        this.setState({
          roles: [
            ...(this.state.roles || []),
            {
              id: role.id,
              name: role.name,
            },
          ],
        })
      })
    } else {
      this.setState({
        roles: [
          ...(this.state.roles || []),
          {
            id: role.id,
            name: role.name,
          },
        ],
      })
    }
  }

  render() {
    const { expiry_date, is_admin, roles, showRoles } = this.state
    const buttonText = this.props.isEdit ? 'Update' : 'Create'
    const buttonSavingText = this.props.isEdit ? 'Updating' : 'Creating'
    return (
      <>
        <div className='modal-body flex flex-column flex-fill px-4'>
          {!this.state.key && (
            <div>
              <Flex className='mb-3 mt-4'>
                <div>
                  <label>Name</label>
                </div>
                <Input
                  value={this.state.name}
                  onChange={(e) =>
                    this.setState({ name: Utils.safeParseEventValue(e) })
                  }
                  isValid={!!this.state.name}
                  type='text'
                  inputClassName='input--wide'
                  placeholder='e.g. Admin API Key'
                />
              </Flex>
              <>
                <Row className='mb-3 mt-4'>
                  <label className='mr-2'>Is admin</label>
                  <Switch
                    onChange={() => {
                      this.setState({
                        is_admin: !is_admin,
                      })
                    }}
                    checked={is_admin}
                  />
                </Row>
                {!is_admin && (
                  <>
                    <Row className='mb-3 mt-4'>
                      <label className='mr-2'>Roles:</label>
                      {roles?.map((r) => (
                        <Row
                          key={r.id}
                          onClick={() =>
                            this.removeRoleApiKey(r.id, this.props.isEdit)
                          }
                          className='chip'
                        >
                          <span className='font-weight-bold'>{r.name}</span>
                          <span className='chip-icon ion'>
                            <IonIcon
                              icon={closeIcon}
                              style={{ fontSize: '13px' }}
                            />
                          </span>
                        </Row>
                      ))}
                    </Row>
                    <Row className='mb-3 mt-4'>
                      <Button
                        theme='text'
                        onClick={() => this.setState({ showRoles: !showRoles })}
                      >
                        Select roles
                      </Button>
                      <div className='px-4'>
                        <MyRoleSelect
                          isRoleApiKey
                          orgId={AccountStore.getOrganisation().id}
                          value={roles?.map((v) => v.id)}
                          onAdd={(role) =>
                            this.addRole(role, this.props.isEdit)
                          }
                          onRemove={(roleId) =>
                            this.removeRoleApiKey(roleId, this.props.isEdit)
                          }
                          isOpen={showRoles}
                          onToggle={() =>
                            this.setState({ showRoles: !showRoles })
                          }
                        />
                      </div>
                    </Row>
                  </>
                )}
              </>
              <Flex>
                <div>
                  <label>Expiry</label>
                </div>
                <DateSelect
                  onChange={(e) => {
                    this.setState({
                      expiry_date: e.toISOString(),
                    })
                  }}
                  selected={expiry_date ? moment(expiry_date)._d : null}
                  value={
                    expiry_date
                      ? `${moment(expiry_date).format('Do MMM YYYY hh:mma')}`
                      : 'Never'
                  }
                />
              </Flex>
            </div>
          )}

          {this.state.key && (
            <div className='mb-4'>
              <InfoMessage>
                Please keep a note of your API key once it's created, we do not
                store it.
              </InfoMessage>

              <Token show token={this.state.key} />
            </div>
          )}
          {this.state.key ? (
            <div />
          ) : (
            <>
              <div className='modal-footer my-5 p-0'>
                <Button
                  disabled={!expiry_date}
                  onClick={() => this.setState({ expiry_date: null })}
                  theme='secondary'
                  className='mr-2'
                >
                  Clear Date
                </Button>
                <Button
                  onClick={
                    this.props.isEdit
                      ? () => this.updateApiKey(this.props.prefix)
                      : this.submit
                  }
                  disabled={
                    this.state.isSaving ||
                    !this.state.name ||
                    (!is_admin && !roles?.length)
                  }
                >
                  {this.state.isSaving ? buttonSavingText : buttonText}
                </Button>
              </div>
            </>
          )}
        </div>
      </>
    )
  }
}

export default class AdminAPIKeys extends PureComponent {
  static displayName = 'TheComponent'

  state = {
    isLoading: false,
    organisationId: null,
  }

  static propTypes = {}

  componentDidMount() {
    this.fetch()
  }

  componentDidUpdate() {
    if (this.props.organisationId === this.state.organisationId) return

    this.fetch()
    this.setState({ organisationId: this.props.organisationId })
  }

  createAPIKey = () => {
    openModal(
      'New Admin API Key',
      <CreateAPIKey
        organisationId={this.props.organisationId}
        onSuccess={() => {
          this.fetch()
        }}
      />,
      'p-0 side-modal',
    )
  }

  editAPIKey = (name, masterAPIKey, prefix) => {
    openModal(
      `${name} API Key`,
      <CreateAPIKey
        isEdit
        masterAPIKey={masterAPIKey}
        prefix={prefix}
        onSuccess={() => {
          this.setState({ isLoading: true })
          this.fetch()
          closeModal()
          toast('API key Updated')
        }}
      />,
      'p-0 side-modal',
    )
  }

  fetch = () => {
    this.setState({ isLoading: true })
    data
      .get(
        `${Project.api}organisations/${this.props.organisationId}/master-api-keys/`,
      )
      .then((res) => {
        this.setState({
          apiKeys: res,
          isLoading: false,
        })
      })
  }

  remove = (v) => {
    openConfirm({
      body: (
        <div>
          This will revoke the API key <strong>{v.name}</strong> ({v.prefix}
          *****************). This change cannot be undone.
        </div>
      ),
      onYes: () => {
        data
          .delete(
            `${Project.api}organisations/${this.props.organisationId}/master-api-keys/${v.prefix}/`,
          )
          .then(() => {
            this.fetch()
          })
      },
      title: 'Revoke the API key',
      yesText: 'Confirm',
    })
  }

  render() {
    const apiKeys = this.state.apiKeys && this.state.apiKeys.results
    return (
      <div>
        <JSONReference
          className='mt-4'
          hideCondensedButton
          title={'API Keys'}
          json={apiKeys}
        />
        <Column className='my-4 ml-0 col-md-6'>
          <h5 className='mb-1'>{`${'Manage'} API Keys`}</h5>
          <p className='mb-0 fs-small lh-sm'>
            {`API keys are used to authenticate with the Admin API.`}
          </p>
          <div className='mb-4 fs-small lh-sm'>
            <Button
              theme='text'
              href='https://docs.flagsmith.com/integrations/terraform#terraform-api-key'
              target='_blank'
              className='fw-normal'
            >
              {`Learn about API Keys.`}
            </Button>
          </div>
          <Button onClick={this.createAPIKey} disabled={this.state.isLoading}>
            {`Create API Key`}
          </Button>
        </Column>
        {this.state.isLoading && (
          <div className='text-center'>
            <Loader />
          </div>
        )}
        {!!apiKeys && !!apiKeys.length && (
          <PanelSearch
            className='no-pad'
            items={apiKeys}
            header={
              <Row className='table-header'>
                <Flex className='table-column px-3'>API Keys</Flex>
                <Flex className='table-column'>Created</Flex>
                <Flex className='table-column'>Is Admin</Flex>
                <Flex className='table-column'>Active</Flex>
                <div
                  className='table-column text-center'
                  style={{ width: '80px' }}
                >
                  Remove
                </div>
              </Row>
            }
            renderRow={(v) =>
              !v.revoked && (
                <Row
                  className='list-item'
                  key={v.id}
                  onClick={() => this.editAPIKey(v.name, v.id, v.prefix)}
                >
                  <Flex className='table-column px-3'>
                    <div className='font-weight-medium mb-1'>{v.name}</div>
                    <div className='list-item-subtitle'>
                      <div>{v.prefix}*****************</div>
                    </div>
                  </Flex>
                  <Flex className='table-column fs-small lh-sm'>
                    {moment(v.created).format('Do MMM YYYY HH:mma')}
                  </Flex>
                  <Flex className='table-column fs-small lh-sm'>
                    <Switch checked={v.is_admin} disabled={true} />
                  </Flex>
                  <Flex className='table-column fs-small lh-sm'>
                    {v.has_expired ? (
                      <div className='ml-1'>
                        <Tooltip title={<Icon name='close-circle' />}>
                          {'This API key has expired'}
                        </Tooltip>
                      </div>
                    ) : (
                      <span className='ml-1'>
                        <Icon
                          name='checkmark-circle'
                          fill='#27AB95'
                          width={28}
                        />
                      </span>
                    )}
                  </Flex>
                  <div
                    className='table-column  text-center'
                    style={{ width: '80px' }}
                  >
                    <Button
                      onClick={(e) => {
                        e.stopPropagation()
                        this.remove(v)
                      }}
                      className='btn btn-with-icon'
                    >
                      <Icon name='trash-2' width={20} fill='#656D7B' />
                    </Button>
                  </div>
                </Row>
              )
            }
          />
        )}
      </div>
    )
  }
}
