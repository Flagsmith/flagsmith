import React from 'react'
import data from 'common/data/base/_data'
import ErrorMessage from './ErrorMessage'
import ConfigProvider from 'common/providers/ConfigProvider'

const SamlForm = class extends React.Component {
  static displayName = 'SamlForm'

  constructor() {
    super()
    this.state = {
      remember: true,
      saml: API.getCookie('saml') || '',
    }
  }

  submit = (e) => {
    if (this.state.isLoading || !this.state.saml) {
      return
    }
    Utils.preventDefault(e)
    this.setState({ error: false, isLoading: true })

    data
      .post(`${Project.api}auth/saml/${this.state.saml}/request/`)
      .then((res) => {
        if (this.state.remember) {
          API.setCookie('saml', this.state.saml)
        }
        if (res.headers && res.headers.Location) {
          document.location.href = res.headers.Location
        } else {
          this.setState({ error: true })
        }
      })
      .catch(() => {
        this.setState({ error: true, isLoading: false })
      })
  }

  render() {
    return (
      <form onSubmit={this.submit} className='saml-form' id='pricing'>
        <InputGroup
          inputProps={{ className: 'full-width' }}
          onChange={(e) =>
            this.setState({ saml: Utils.safeParseEventValue(e) })
          }
          value={this.state.saml}
          type='text'
          title='Organisation Name'
        />
        {this.state.error && (
          <ErrorMessage error='Please check your organisation name and try again.' />
        )}

        <Row className='text-right mb-4'>
          <Flex />
          <input
            onChange={() => {
              const remember = !this.state.remember
              if (!remember) {
                API.setCookie('saml', null)
              }
              this.setState({ remember })
            }}
            id='organisation'
            className='mr-2'
            type='checkbox'
            checked={this.state.remember}
          />
          <label className='mb-0' htmlFor='organisation'>
            Remember this SAML organisation
          </label>
        </Row>

        <div className='text-right'>
          <Button
            type='submit'
            disabled={!this.state.saml || this.state.isLoading}
          >
            Continue
          </Button>
        </div>
      </form>
    )
  }
}

SamlForm.propTypes = {
  children: RequiredElement,
  defaultValue: OptionalBool,
  title: RequiredString,
  toggleComponent: OptionalFunc,
}

module.exports = ConfigProvider(SamlForm)
