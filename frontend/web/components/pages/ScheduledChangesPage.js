import React, { Component } from 'react'
import ChangeRequestStore from 'common/stores/change-requests-store'
import OrganisationStore from 'common/stores/organisation-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import JSONReference from 'components/JSONReference'
import Icon from 'components/Icon'
import PageTitle from 'components/PageTitle'
import { Link, withRouter } from 'react-router-dom'
import PlanBasedBanner, {
  featureDescriptions,
} from 'components/PlanBasedAccess'

const ChangeRequestsPage = class extends Component {
  static displayName = 'ChangeRequestsPage'

  constructor(props, context) {
    super(props, context)
    this.state = {
      live_after: new Date().toISOString(),
      showArchived: false,
      tags: [],
    }
    ES6Component(this)
    this.listenTo(ChangeRequestStore, 'change', () => this.forceUpdate())
    this.listenTo(OrganisationStore, 'change', () => this.forceUpdate())
  }
  componentDidMount = () => {
    AppActions.getChangeRequests(this.props.match.params.environmentId, {})
    AppActions.getChangeRequests(this.props.match.params.environmentId, {
      committed: true,
    })
    AppActions.getChangeRequests(this.props.match.params.environmentId, {
      live_from_after: this.state.live_after,
    })
    AppActions.getOrganisation(AccountStore.getOrganisation().id)
  }

  render() {
    const { environmentId, projectId } = this.props.match.params
    const dataPaging =
      ChangeRequestStore.model &&
      ChangeRequestStore.model[environmentId] &&
      ChangeRequestStore.model[environmentId] &&
      ChangeRequestStore.model[environmentId]

    const dataScheduled =
      ChangeRequestStore.scheduled &&
      ChangeRequestStore.scheduled[environmentId] &&
      ChangeRequestStore.scheduled[environmentId].results
    const dataScheduledPaging =
      ChangeRequestStore.scheduled &&
      ChangeRequestStore.scheduled[environmentId] &&
      ChangeRequestStore.scheduled[environmentId]

    return (
      <div
        data-test='change-requests-page'
        id='change-requests-page'
        className='app-container container'
      >
        {!!Utils.getPlansPermission('SCHEDULE_FLAGS') && (
          <PageTitle title={featureDescriptions.SCHEDULE_FLAGS.title}>
            {featureDescriptions.SCHEDULE_FLAGS.description}
          </PageTitle>
        )}
        <PlanBasedBanner feature={'SCHEDULE_FLAGS'} theme={'page'}>
          <Flex>
            {
              <div>
                <PanelSearch
                  renderSearchWithNoResults
                  id='users-list'
                  title='Scheduled Changes'
                  className='no-pad'
                  isLoading={
                    ChangeRequestStore.isLoading ||
                    !dataScheduled ||
                    !OrganisationStore.model
                  }
                  items={dataScheduled}
                  renderFooter={() => (
                    <JSONReference
                      className='mt-4 ml-3'
                      title={'Change Requests'}
                      json={dataScheduled}
                    />
                  )}
                  paging={dataScheduledPaging}
                  nextPage={() =>
                    AppActions.getChangeRequests(
                      this.props.match.params.environmentId,
                      { live_from_after: this.state.live_after },
                      dataPaging.next,
                    )
                  }
                  prevPage={() =>
                    AppActions.getChangeRequests(
                      this.props.match.params.environmentId,
                      { live_from_after: this.state.live_after },
                      dataPaging.previous,
                    )
                  }
                  goToPage={(page) =>
                    AppActions.getChangeRequests(
                      this.props.match.params.environmentId,
                      { live_from_after: this.state.live_after },
                      `${Project.api}environments/${environmentId}/list-change-requests/?page=${page}`,
                    )
                  }
                  renderRow={({ created_at, id, title, user: _user }) => {
                    const user =
                      OrganisationStore.model &&
                      OrganisationStore.model.users.find((v) => v.id === _user)
                    return (
                      <Link
                        to={`/project/${projectId}/environment/${environmentId}/scheduled-changes/${id}`}
                        className='flex-row list-item clickable'
                      >
                        <Flex className='table-column px-3'>
                          <div className='font-weight-medium'>{title}</div>
                          <div className='list-item-subtitle mt-1'>
                            Created{' '}
                            {moment(created_at).format('Do MMM YYYY HH:mma')} by{' '}
                            {user && user.first_name} {user && user.last_name}
                          </div>
                        </Flex>
                        <div className='table-column'>
                          <Icon
                            name='chevron-right'
                            fill='#9DA4AE'
                            width={20}
                          />
                        </div>
                      </Link>
                    )
                  }}
                />
              </div>
            }
          </Flex>
        </PlanBasedBanner>
      </div>
    )
  }
}

ChangeRequestsPage.propTypes = {}

module.exports = withRouter(ConfigProvider(ChangeRequestsPage))
