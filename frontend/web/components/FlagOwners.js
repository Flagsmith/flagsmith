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
import OrganisationProvider from 'common/providers/OrganisationProvider'

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
    return (
      <OrganisationProvider>
        {({ users }) => {
          const ownerUsers = this.getOwners(users, this.state.owners || [])
          return (
            <div>
              <SettingsButton
                content={
                  <Row style={{ rowGap: '12px' }}>
                    {ownerUsers.map((u) => (
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
                }
                feature={'FLAG_OWNERS'}
                onClick={() => {
                  this.setState({ showUsers: !this.state.showUsers })
                }}
              >
                Assigned users
              </SettingsButton>

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
        }}
      </OrganisationProvider>
    )
  }
}

export default ConfigProvider(TheComponent)
