import React, { Component } from 'react'
import Highlight from './Highlight'
import PlayIcon from './svg/PlayIcon'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'

const TryIt = class extends Component {
  static displayName = 'TryIt'

  constructor(props, context) {
    super(props, context)
    this.state = {}
  }

  request = () => {
    const { environmentId, userId } = this.props
    this.setState({ isLoading: true })
    API.trackEvent(Constants.events.TRY_IT)

    const url = userId
      ? `${Utils.getSDKEndpoint()}identities/?identifier=${encodeURIComponent(
          userId,
        )}`
      : `${Utils.getSDKEndpoint()}flags/`
    const options = {
      headers: { 'X-Environment-Key': environmentId },
    }

    if (E2E && document.getElementById('e2e-request')) {
      const payload = {
        options,
        url,
      }
      document.getElementById('e2e-request').innerText = JSON.stringify(payload)
    }

    fetch(url, options)
      .then((res) => res.json())
      .then((data) => {
        let res = {}
        if (userId) {
          res.features = {}
          res.traits = {}
        }
        const features = userId ? data.flags : data
        features.map(({ enabled, feature, feature_state_value }) => {
          ;(userId ? res.features : res)[feature.name] = {
            enabled,
            value: feature_state_value,
          }
        })
        if (userId) {
          data.traits.map(({ trait_key, trait_value }) => {
            res.traits[trait_key] = trait_value
          })
        }
        res = JSON.stringify(res, null, 2)
        this.setState({ data: res, isLoading: false })
        toast('Retrieved results')
      })
  }

  render() {
    return Utils.getFlagsmithHasFeature('try_it') ? (
      <Panel icon='ion-md-code' title='Try it out'>
        <div>
          <div className='text-center'>
            <p className='faint-lg'>{this.props.title}</p>
            <div>
              <Button
                id='try-it-btn'
                disabled={this.state.isLoading}
                onClick={this.request}
                className='btn btn--with-icon primary'
              >
                {this.state.data ? 'Test again' : 'Run test'}{' '}
                <PlayIcon className='btn__icon btn__icon--small' alt='Run' />
              </Button>
            </div>
          </div>
          {this.state.data && (
            <div id={!this.state.isLoading && 'try-it-results'}>
              <FormGroup />
              <div
                style={{ opacity: this.state.isLoading ? 0.5 : 1 }}
                className='fade '
              >
                <Highlight forceExpanded className='json'>
                  {this.state.data}
                </Highlight>
              </div>
            </div>
          )}
          {this.state.isLoading && !this.state.data && (
            <div className='text-center'>
              <Loader />
            </div>
          )}
        </div>
      </Panel>
    ) : (
      <div />
    )
  }
}

TryIt.propTypes = {}

module.exports = ConfigProvider(TryIt)
