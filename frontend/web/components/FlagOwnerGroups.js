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
import ConnectedGroupSelect from './ConnectedGroupSelect'
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
    return (
      <OrganisationProvider>
        {({ groups }) => {
          return (
            <div>
              <SettingsButton
                feature='FLAG_OWNERS'
                content={
                  <ConnectedGroupSelect
                    orgId={AccountStore.getOrganisation()?.id}
                    showValues
                    groups={groups}
                    value={this.state.groupOwners}
                    isOpen={this.state.showUsers}
                    onAdd={this.addOwner}
                    onRemove={this.removeOwner}
                    onToggle={() =>
                      this.setState({ showUsers: !this.state.showUsers })
                    }
                  />
                }
                onClick={() => {
                  this.setState({ showUsers: true })
                }}
              >
                Assigned groups
              </SettingsButton>
            </div>
          )
        }}
      </OrganisationProvider>
    )
  }
}

export default ConfigProvider(TheComponent)
