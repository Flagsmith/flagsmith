import React, { Component } from 'react'
import data from 'common/data/base/_data'
import UserSelect from './UserSelect'
import ConfigProvider from 'common/providers/ConfigProvider'
import Icon from './Icon'
import { close } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

class TheComponent extends Component {
  state = {}
  componentDidMount() {
    this.getData()
  }

  getData = () => {
    data
      .get(
        `${Project.api}projects/${this.props.projectId}/features/${this.props.id}/`,
      )
      .then((res) => {
        const owners = (res.owners || []).map((v) => v.id)
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
              <Row
                className='clickable'
                onClick={() => {
                  if (hasPermission) this.setState({ showUsers: true })
                }}
              >
                <label className='cols-sm-2 control-label'>
                  Assignees <Icon name='setting' width={20} fill={'#656D7B'} />
                </label>
              </Row>
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
                {!ownerUsers.length && <div>This flag has no assignees</div>}
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
