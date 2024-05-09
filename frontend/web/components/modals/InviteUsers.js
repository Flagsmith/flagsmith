import React, { Component } from 'react'
import Button from 'components/base/forms/Button'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import Icon from 'components/Icon'
import { add } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

const InviteUsers = class extends Component {
  static displayName = 'InviteUsers'

  constructor(props, context) {
    super(props, context)
    this.state = {
      invites: [{}],
      name: props.name,
      tab: 0,
    }
  }

  close(invites) {
    AppActions.inviteUsers(invites)
    closeModal()
  }

  componentDidMount = () => {
    this.focusTimeout = setTimeout(() => {
      this.input.focus()
      this.focusTimeout = null
    }, 500)
  }

  componentWillUnmount() {
    if (this.focusTimeout) {
      clearTimeout(this.focusTimeout)
    }
  }

  isValid = () =>
    _.every(
      this.state.invites,
      (invite) => Utils.isValidEmail(invite.emailAddress) && invite.role,
    )

  onChange = (index, key, value) => {
    const invites = this.state.invites
    invites[index][key] = value
    this.setState({ invites })
  }

  deleteInvite = (index) => {
    const invites = this.state.invites
    invites.splice(index, 1)
    this.setState({ invites })
  }

  changeTab = (tab) => {
    this.setState({
      invites: [{}],
      tab,
    })
  }

  render() {
    const { invites } = this.state
    const hasRbacPermission = Utils.getPlansPermission('RBAC')

    return (
      <OrganisationProvider>
        {({ error, isSaving }) => (
          <div>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                AppActions.inviteUsers(invites)
              }}
            >
              <div className='modal-body px-4 pt-4'>
                <Row>
                  <Flex>
                    <label>Email Address</label>
                  </Flex>
                  <Flex>
                    <label>Select Role</label>
                  </Flex>
                </Row>
                {_.map(invites, (invite, index) => (
                  <Row className='mb-2' key={index}>
                    <Flex>
                      <InputGroup
                        className='mb-2'
                        ref={(e) => (this.input = e)}
                        inputProps={{
                          className: 'full-width',
                          name: 'inviteEmail',
                        }}
                        onChange={(e) =>
                          this.onChange(
                            index,
                            'emailAddress',
                            Utils.safeParseEventValue(e),
                          )
                        }
                        value={invite.emailAddress}
                        isValid={this.isValid}
                        type='text'
                        placeholder='E-mail address'
                      />
                    </Flex>
                    <Flex className='mb-2' style={{ position: 'relative' }}>
                      <Select
                        data-test='select-role'
                        placeholder='Select a role'
                        value={invite.role}
                        onChange={(role) => this.onChange(index, 'role', role)}
                        className='pl-2 react-select'
                        options={_.map(Constants.roles, (label, value) => ({
                          isDisabled: value !== 'ADMIN' && !hasRbacPermission,
                          label:
                            value !== 'ADMIN' && !hasRbacPermission
                              ? `${label} - Please upgrade for role based access`
                              : label,
                          value,
                        }))}
                      />
                    </Flex>
                    {invites.length > 1 ? (
                      <div className='ml-2'>
                        <Button
                          id='delete-invite'
                          type='button'
                          onClick={() => this.deleteInvite(index)}
                          className='btn btn-with-icon mb-2'
                        >
                          <Icon name='trash-2' width={20} fill='#656D7B' />
                        </Button>
                      </div>
                    ) : (
                      <div />
                    )}
                  </Row>
                ))}

                <div className='text-right mt-4'>
                  <Button
                    theme='outline'
                    size='small'
                    id='btn-add-invite'
                    disabled={isSaving || !this.isValid()}
                    type='button'
                    onClick={() =>
                      this.setState({
                        invites: this.state.invites.concat([{}]),
                      })
                    }
                  >
                    <Row>
                      <span className='pl-2 icon'>
                        <IonIcon icon={add} style={{ fontSize: '13px' }} />
                      </span>
                      <span>
                        {isSaving ? 'Sending' : 'Invite additional member'}
                      </span>
                    </Row>
                  </Button>
                </div>

                <div className='mt-5'>
                  Users without administrator privileges will need to be invited
                  to individual projects.
                  <div>
                    <Button
                      theme='text'
                      target='_blank'
                      href='https://docs.flagsmith.com/system-administration/rbac'
                      className='fw-normal'
                    >
                      Learn about User Roles.
                    </Button>
                  </div>
                </div>
                {error && <Error error={error} />}
              </div>
              <div className='modal-footer pt-5'>
                <Button
                  id='btn-send-invite'
                  disabled={isSaving || !this.isValid()}
                  onClick={() => this.close(invites)}
                  type='submit'
                >
                  {isSaving ? 'Sending' : 'Send Invitation'}
                </Button>
              </div>
            </form>
          </div>
        )}
      </OrganisationProvider>
    )
  }
}

InviteUsers.propTypes = {}

export default ConfigProvider(InviteUsers)
