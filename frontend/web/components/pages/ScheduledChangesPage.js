import React, { Component } from 'react'
import ChangeRequestStore from 'common/stores/change-requests-store'
import OrganisationStore from 'common/stores/organisation-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import PaymentModal from 'components/modals/Payment'
import JSONReference from 'components/JSONReference'
import InfoMessage from 'components/InfoMessage'

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
        <Flex>
          <h4>Scheduled Changes</h4>
          {
            <div>
              {!hasSchedulePlan ? (
                <div className='mt-2'>
                  <InfoMessage>
                    Schedule feature state changes with a Change Request flow
                    with our{' '}
                    <Button
                      theme='text'
                      onClick={() => {
                        openModal(
                          'Payment plans',
                          <PaymentModal viewOnly={false} />,
                          'modal-lg',
                        )
                      }}
                    >
                      Start-up plan
                    </Button>
                    . Find out more{' '}
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
                  <p>
                    Manage feature state changes that have been scheduled to go
                    live.
                  </p>
                  <PanelSearch
                    renderSearchWithNoResults
                    id='users-list'
                    title='Scheduled Changes'
                    className='mt-4'
                    isLoading={
                      ChangeRequestStore.isLoading ||
                      !dataScheduled ||
                      !OrganisationStore.model
                    }
                    icon='ion-ios-timer'
                    items={dataScheduled}
                    renderFooter={() => (
                      <JSONReference
                        className='mt-4'
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
                        >
                          <Row className='list-item clickable'>
                            <span className='ion text-primary mr-4 icon ion-ios-timer' />
                            <div>
                              <Button theme='text'>{title}</Button>
                              <div className='list-item-footer faint'>
                                Created at{' '}
                                {moment(created_at).format(
                                  'Do MMM YYYY HH:mma',
                                )}{' '}
                                by {user && user.first_name}{' '}
                                {user && user.last_name}
                              </div>
                            </div>
                          </Row>
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
