import React, { Component } from 'react'
import data from 'common/data/base/_data'
import ConfigProvider from 'common/providers/ConfigProvider'

const UserPage = class extends Component {
  static displayName = 'UserPage'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = {
      preselect: Utils.fromParam().flag,
      tags: [],
    }
  }

  componentDidMount() {
    const {
      match: { params },
    } = this.props
    data
      .get(
        `${Project.api}environments/${
          params.environmentId
        }/${Utils.getIdentitiesEndpoint()}/?q="${params.identity}"`,
      )
      .then((res) => {
        const user = res.results[0]
        if (user) {
          this.props.history.replace(
            `/project/${params.projectId}/environment/${
              params.environmentId
            }/users/${params.identity}/${user.identity || user.identity_uuid}`,
          )
        } else {
          this.props.history.replace(
            `/project/${params.projectId}/environment/${params.environmentId}/users/`,
          )
        }
      })
  }

  render() {
    return (
      <div className='app-container'>
        <div className='text-center'>
          <Loader />
        </div>
      </div>
    )
  }
}

UserPage.propTypes = {}

module.exports = ConfigProvider(UserPage)
