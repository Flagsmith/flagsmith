import React, { Component } from 'react'
import Constants from 'common/constants'
import { withRouter } from 'react-router-dom'
const InvitePage = class extends Component {
  static displayName = 'InvitePage'

  constructor(props, context) {
    super(props, context)
    this.state = {}
    AppActions.acceptInvite(this.props.match.params.id)
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.INVITE)
  }

  onSave = (id) => {
    AppActions.selectOrganisation(id)
    this.props.history.replace(Utils.getOrganisationHomePage(id))
  }

  render() {
    return (
      <div className='app-container'>
        <AccountProvider onSave={this.onSave}>
          {({ error }) => (
            <div className='centered-container'>
              <div>
                {error ? (
                  <div>
                    <h3 className='pt-5'>Oops</h3>
                    <p>
                      We could not validate your invite, please check the invite
                      URL and email address you have entered is correct.
                    </p>
                  </div>
                ) : (
                  <Loader />
                )}
              </div>
            </div>
          )}
        </AccountProvider>
      </div>
    )
  }
}

InvitePage.propTypes = {}

module.exports = withRouter(InvitePage)
