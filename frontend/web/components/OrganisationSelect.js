import React, { Component } from 'react'
import NavLink from 'react-router-dom/NavLink'
import Icon from './Icon'

const OrganisationSelect = class extends Component {
  static displayName = 'OrganisationSelect'

  constructor(props, context) {
    super(props, context)
    this.state = {}
  }

  render() {
    return (
      <AccountProvider>
        {({ user }) => (
          <Row>
            <div style={{ width: '500px' }}>
              <Select
                value={{
                  label: AccountStore.getOrganisation().name,
                  value: AccountStore.getOrganisation().id,
                }}
                onChange={({ value }) => {
                  API.setCookie('organisation', `${value}`)
                  this.props.onChange && this.props.onChange(value)
                }}
                options={
                  user &&
                  user.organisations &&
                  user.organisations.map((organisation) => {
                    return { label: organisation.name, value: organisation.id }
                  })
                }
              />
            </div>
            {AccountStore.getOrganisationRole() === 'ADMIN' && (
              <NavLink
                id='organisation-settings-link'
                activeClassName='active'
                className='btn btn-with-icon ml-3'
                to='/organisation-settings'
              >
                <Icon name='setting' fill='#656D7B' />
              </NavLink>
            )}

            {user &&
              user.organisations &&
              user.organisations.map((organisation) => (
                <div key={organisation.id}></div>
              ))}
          </Row>
        )}
      </AccountProvider>
    )
  }
}

OrganisationSelect.propTypes = {}

module.exports = OrganisationSelect
