import React, { Component } from 'react'
import data from 'common/data/base/_data'
import UserSelect from './UserSelect'
import ConfigProvider from 'common/providers/ConfigProvider'
import Icon from './Icon'
import { close } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'
import { getProjectFlag } from 'common/services/useProjectFlag'
import { getStore } from 'common/store'
import SettingsButton from './SettingsButton'

class TheComponent extends Component {
  state = {}
  componentDidMount() {
    this.getData()
  }

  getData = () => {
    getProjectFlag(getStore(), {
      id: this.props.id,
      project: this.props.projectId,
    }).then((res) => {
      const owners = (res.data.owners || []).map((v) => v.id)
      this.setState({ owners })
    })
  }

  addOwner = (id) => {
    this.setState({ owners: (this.state.owners || []).concat(id) })
    data.post(
      `${Project.api}projects/${this.props.projectId}/features/${this.props.id}/add-owners/`,
      {
        user_ids: [id],
      },
    )
  }

  removeOwner = (id) => {
    this.setState({ owners: (this.state.owners || []).filter((v) => v !== id) })
    data.post(
      `${Project.api}projects/${this.props.projectId}/features/${this.props.id}/remove-owners/`,
      {
        user_ids: [id],
      },
    )
  }

  getOwners = (users, owners) =>
    users ? users.filter((v) => owners.includes(v.id)) : []

  render() {
    const hasPermission = Utils.getPlansPermission('FLAG_OWNERS')

    return (
      <OrganisationProvider>
        {({ users }) => {
          const ownerUsers = this.getOwners(users, this.state.owners || [])
          const res = (
            <div>
              <SettingsButton
                onClick={() => {
                  if (hasPermission) this.setState({ showUsers: true })
                }}
              >
                Assigned users
              </SettingsButton>
              <Row style={{ rowGap: '12px' }}>
                {hasPermission &&
                  ownerUsers.map((u) => (
                    <Row
                      key={u.id}
                      onClick={() => this.removeOwner(u.id)}
                      className='chip mr-2'
                    >
                      <span className='font-weight-bold'>
                        {u.first_name} {u.last_name}
                      </span>
                      <span className='chip-icon ion'>
                        <IonIcon icon={close} />
                      </span>
                    </Row>
                  ))}
                {!ownerUsers.length && (
                  <div>This flag has no assigned users</div>
                )}
              </Row>

              <UserSelect
                users={users}
                value={this.state.owners}
                onAdd={this.addOwner}
                onRemove={this.removeOwner}
                isOpen={this.state.showUsers}
                onToggle={() =>
                  this.setState({ showUsers: !this.state.showUsers })
                }
              />
            </div>
          )
          return hasPermission ? (
            res
          ) : (
            <div>
              {res}
              The add flag assignees feature is available with our{' '}
              <strong>Scale-up</strong> plan.
            </div>
          )
        }}
      </OrganisationProvider>
    )
  }
}

export default ConfigProvider(TheComponent)
