import React, { Component } from 'react'
import data from 'common/data/base/_data'
import UserSelect from './UserSelect'
import ConfigProvider from 'common/providers/ConfigProvider'
import Icon from './Icon'
import { close } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'
import GroupSelect from './GroupSelect'
import { getProjectFlag } from 'common/services/useProjectFlag'
import { getStore } from 'common/store'

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
      const groupOwners = (res.data.group_owners || []).map((v) => v.id)
      this.setState({ groupOwners })
    })
  }

  addOwner = (id) => {
    this.setState({ groupOwners: (this.state.groupOwners || []).concat(id) })
    data.post(
      `${Project.api}projects/${this.props.projectId}/features/${this.props.id}/add-group-owners/`,
      {
        group_ids: [id],
      },
    )
  }

  removeOwner = (id) => {
    this.setState({
      groupOwners: (this.state.groupOwners || []).filter((v) => v !== id),
    })
    data.post(
      `${Project.api}projects/${this.props.projectId}/features/${this.props.id}/remove-group-owners/`,
      {
        group_ids: [id],
      },
    )
  }

  getGroupOwners = (users, groupOwners) =>
    users ? users.filter((v) => groupOwners.includes(v.id)) : []

  render() {
    const hasPermission = Utils.getPlansPermission('FLAG_OWNERS')

    return (
      <OrganisationProvider>
        {({ groups }) => {
          const ownerUsers = this.getGroupOwners(
            groups,
            this.state.groupOwners || [],
          )
          const res = (
            <div>
              <Row
                className='clickable'
                onClick={() => {
                  if (hasPermission) this.setState({ showUsers: true })
                }}
              >
                <label className='cols-sm-2 control-label'>
                  Assigned groups{' '}
                  <Icon name='setting' width={20} fill={'#656D7B'} />
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
                      <span className='font-weight-bold'>{u.name}</span>
                      <span className='chip-icon ion'>
                        <IonIcon icon={close} />
                      </span>
                    </Row>
                  ))}
                {!ownerUsers.length && (
                  <div>This flag has no assigned groups</div>
                )}
              </Row>
              <GroupSelect
                groups={groups}
                value={this.state.groupOwners}
                isOpen={this.state.showUsers}
                size={null}
                onAdd={this.addOwner}
                onRemove={this.removeOwner}
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
