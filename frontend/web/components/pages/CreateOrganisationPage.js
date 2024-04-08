import React, { Component } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import PageTitle from 'components/PageTitle'
import CondensedRow from 'components/CondensedRow'

class CreateOrganisationPage extends Component {
  static displayName = 'CreateOrganisastionPage'

  constructor(props, context) {
    super(props, context)
    this.state = { name: '' }
  }

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.CREATE_ORGANISATION)
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

  onSave = (id) => {
    AppActions.selectOrganisation(id)
    API.setCookie('organisation', `${id}`)
    this.context.router.history.push('/organisation-settings')
  }

  render() {
    if (Project.superUserCreateOnly && !AccountStore.model.is_superuser) {
      return (
        <div className='text-center alert'>
          Your Flagsmith instance is setup to only allow super users to create
          an organisation, please contact your administrator.
        </div>
      )
    }
    if (Utils.getFlagsmithHasFeature('disable_create_org')) {
      return (
        <div id='create-org-page' className='container app-container'>
          This Flagsmith instance is configured to prevent additional
          organisations from being created. Please contact an administrator. If
          you think you are seeing this page by mistake, please check you are
          invited to the correct organisation.
        </div>
      )
    }
    return (
      <div id='create-org-page' className='container app-container'>
        <PageTitle title={'Create your organisation'}>
          Organisations allow you to manage multiple projects within a team.
        </PageTitle>
        <AccountProvider onSave={this.onSave}>
          {({ isSaving }, { createOrganisation }) => (
            <form
              onSubmit={(e) => {
                e.preventDefault()
                if (Project.capterraKey) {
                  const parts = Project.capterraKey.split(',')
                  Utils.appendImage(
                    `https://ct.capterra.com/capterra_tracker.gif?vid=${parts[0]}&vkey=${parts[1]}`,
                  )
                }
                createOrganisation(this.state.name)
              }}
            >
              <CondensedRow>
                <InputGroup
                  ref={(e) => (this.input = e)}
                  inputProps={{ className: 'full-width', name: 'orgName' }}
                  title='Organisation Name'
                  placeholder='E.g. ACME Ltd'
                  onChange={(e) =>
                    this.setState({ name: Utils.safeParseEventValue(e) })
                  }
                  className='mb-5'
                />
                <div className='text-right'>
                  <Button
                    type='submit'
                    disabled={isSaving || !this.state.name}
                    id='create-org-btn'
                  >
                    Create Organisation
                  </Button>
                </div>
              </CondensedRow>
            </form>
          )}
        </AccountProvider>
      </div>
    )
  }
}

export default ConfigProvider(CreateOrganisationPage)
