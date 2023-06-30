import React, { Component } from 'react'
import cx from 'classnames'
import NavLink from 'react-router-dom/NavLink'

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
          <div>
            {user &&
              user.organisations &&
              user.organisations.map((organisation) => (
                <div key={organisation.id}>
                  <Row
                    className={cx('popover-bt__list-item', {
                      active:
                        AccountStore.getOrganisation().id === organisation.id,
                    })}
                  >
                    <a
                      href='#'
                      onClick={() => {
                        API.setCookie('organisation', `${organisation.id}`)
                        this.props.onChange && this.props.onChange(organisation)
                      }}
                    >
                      {organisation.name}
                    </a>
                    {AccountStore.getOrganisationRole() === 'ADMIN' && (
                      <NavLink
                        id='organisation-settings-link'
                        activeClassName='active'
                        onClick={() => {
                          this.props.onChange &&
                            this.props.onChange(organisation)
                        }}
                        className='btn btn-link text-nowrap btn-sm edit'
                        to='/organisation-settings'
                      >
                        <span
                          style={{ fontSize: 16, marginRight: 4 }}
                          className='icon--primary ion ion-md-settings'
                        />
                        {'Manage'}
                      </NavLink>
                    )}
                  </Row>
                </div>
              ))}
          </div>
        )}
      </AccountProvider>
    )
  }
}

OrganisationSelect.propTypes = {}

module.exports = OrganisationSelect
