import React, { Component } from 'react'
import ChangeRequestStore from 'common/stores/change-requests-store'
import OrganisationStore from 'common/stores/organisation-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import JSONReference from 'components/JSONReference'
import InfoMessage from 'components/InfoMessage'
import Icon from 'components/Icon'
import PageTitle from 'components/PageTitle'
import { Link } from 'react-router-dom'
import Constants from 'common/constants'

const ChangeRequestsPage = class extends Component {
  static displayName = 'ChangeRequestsPage'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

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

    const hasSchedulePlan = Utils.getPlansPermission('SCHEDULE_FLAGS')

    return (
      <div
        data-test='change-requests-page'
        id='change-requests-page'
        className='app-container container'
      >
        <PageTitle title={'Scheduling'}>
          Manage feature state changes that have been scheduled to go live.
        </PageTitle>
        <Flex>
          {
            <div>
              {!hasSchedulePlan ? (
                <div className='mt-2'>
                  <InfoMessage>
                    Schedule feature state changes with a Change Request flow
                    with our{' '}
                    <Link to={Constants.upgradeURL}>Start-up plan</Link>. Find
                    out more{' '}
                    <Button
                      theme='text'
                      href='https://docs.flagsmith.com/advanced-use/scheduled-flags#creating-a-stand-alone-scheduled-flag-change'
                      target='_blank'
                    >
                      here
                    </Button>
                    .
                  </InfoMessage>
                </div>
              ) : (
                <>
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
                        OrganisationStore.model.users.find(
                          (v) => v.id === _user,
                        )
                      return (
                        <Link
                          to={`/project/${projectId}/environment/${environmentId}/scheduled-changes/${id}`}
                          className='flex-row list-item clickable'
                        >
                          <Flex className='table-column px-3'>
                            <div className='font-weight-medium'>{title}</div>
                            <div className='list-item-subtitle mt-1'>
                              Created{' '}
                              {moment(created_at).format('Do MMM YYYY HH:mma')}{' '}
                              by {user && user.first_name}{' '}
                              {user && user.last_name}
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
                </>
              )}
            </div>
          }
        </Flex>
      </div>
    )
  }
}

ChangeRequestsPage.propTypes = {}

module.exports = ConfigProvider(ChangeRequestsPage)
