import React, { Component } from 'react'

const OrganisationSelect = class extends Component {
  static displayName = 'OrganisationSelect'

  constructor(props, context) {
    super(props, context)
    this.state = {}
  }

  componentDidMount() {
    if (localStorage.lastEnv) {
      const organisationId = JSON.parse(localStorage.lastEnv).organisationId
      if (this.props.firstOrganisation && organisationId) {
        this.props.onChange(organisationId)
      }
    }
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
                  value: AccountStore.getOrganisationId(),
                }}
                onChange={({ value }) => {
                  this.props.onChange && this.props.onChange(value)
                }}
                options={
                  user &&
                  user.organisations &&
                  user.organisations.map((organisation) => {
                    return { label: organisation.name, value: organisation.id }
                  })
                }
                className='select-lg react-select'
              />
            </div>
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

export default OrganisationSelect
