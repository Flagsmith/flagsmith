import React, { Component } from 'react'
import EnvironmentSelect from 'components/EnvironmentSelect'
import _data from 'common/data/base/_data'
import ErrorMessage from 'components/ErrorMessage'
import ModalHR from './ModalHR'
import Button from 'components/base/forms/Button'
import classNames from 'classnames'
const CreateEditIntegration = class extends Component {
  static displayName = 'CreateEditIntegration'

  constructor(props, context) {
    super(props, context)
    const fields = _.cloneDeep(this.props.integration.fields)
    this.state = {
      data: this.props.data ? { ...this.props.data } : { fields },
      fields,
    }
    if (this.props.id === 'slack' && this.state.data.flagsmithEnvironment) {
      _data
        .get(
          `${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}-channels?limit=1000`,
        )
        .then((res) => {
          this.state.data.enabled = true
          this.state.fields = this.state.fields || []
          this.state.fields.push({
            key: 'channel_id',
            label: 'Channel',
            options: ((res && res.channels) || []).map((v) => ({
              label: v.channel_name,
              value: v.channel_id,
            })),
          })
          this.setState({ authorised: true })
        })
    }
  }

  update = (key, e) => {
    this.setState({
      data: {
        ...this.state.data,
        [key]: Utils.safeParseEventValue(e),
      },
    })
  }

  onComplete = () => {
    closeModal()
    this.props.onComplete && this.props.onComplete()
  }

  submit = (e) => {
    const isOauth = this.props.integration.isOauth && !this.state.authorised
    const isEdit = this.props.data && this.props.data.id
    Utils.preventDefault(e)
    if (this.state.isLoading) {
      return
    }
    this.setState({ isLoading: true })
    const handleOauthSignature = (res, isProject) => {
      const signature = res && res.signature
      if (signature) {
        const postfix = `?redirect_url=${encodeURIComponent(
          `${document.location.href}?environment=${this.state.data.flagsmithEnvironment}&configure=${this.props.id}`,
        )}&signature=${signature}`
        document.location = isProject
          ? `${Project.api}projects/${this.props.projectId}/integrations/${this.props.id}/oauth/${postfix}`
          : `${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}/oauth/${postfix}`
      }
    }
    if (this.props.integration.perEnvironment) {
      if (isOauth) {
        return _data
          .get(
            `${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}/signature/`,
            {
              redirect_url: document.location.href,
            },
          )
          .then((res) => handleOauthSignature(res, false))
      }
      if (isEdit) {
        _data
          .put(
            `${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}/${this.props.data.id}/`,
            this.state.data,
          )
          .then(this.onComplete)
          .catch(this.onError)
      } else {
        _data
          .post(
            `${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}/`,
            this.state.data,
          )
          .then(this.onComplete)
          .catch(this.onError)
      }
    } else if (isOauth) {
      return _data
        .get(
          `${Project.api}projects/${this.props.projectId}/integrations/${this.props.id}/signature/`,
          {
            redirect_url: document.location.href,
          },
        )
        .then((res) => handleOauthSignature(res, true))
    } else if (isEdit) {
      _data
        .put(
          `${Project.api}projects/${this.props.projectId}/integrations/${this.props.id}/${this.props.data.id}/`,
          this.state.data,
        )
        .then(this.onComplete)
        .catch(this.onError)
    } else {
      _data
        .post(
          `${Project.api}projects/${this.props.projectId}/integrations/${this.props.id}/`,
          this.state.data,
        )
        .then(this.onComplete)
        .catch(this.onError)
    }
  }

  onError = (res) => {
    const defaultError =
      'There was an error adding your integration. Please check the details and try again.'
    res
      .text()
      .then((error) => {
        let err = error
        try {
          err = JSON.parse(error)
          this.setState({
            error: err[0] || defaultError,
            isLoading: false,
          })
        } catch (e) {}
      })
      .catch(() => {
        this.setState({
          error: defaultError,
          isLoading: false,
        })
      })
  }

  render() {
    return (
      <form
        className={classNames({
          'px-4 h-100': !!this.props.modal,
        })}
        onSubmit={this.submit}
      >
        <div className={classNames({ 'pt-4': !!this.props.modal })}>
          {this.props.integration.perEnvironment && (
            <div className='mb-3'>
              <label className={!this.props.modal ? 'mb-1 fw-bold' : ''}>
                Flagsmith Environment
              </label>
              <EnvironmentSelect
                readOnly={!!this.props.data || this.props.readOnly}
                value={this.state.data.flagsmithEnvironment}
                onChange={(environment) =>
                  this.update('flagsmithEnvironment', environment)
                }
              />
            </div>
          )}
          {this.state.fields &&
            this.state.fields.map((field) => (
              <>
                <div>
                  <label
                    htmlFor={field.label.replace(/ /g, '')}
                    className={!this.props.modal ? 'mb-1 fw-bold' : ''}
                  >
                    {field.label}
                  </label>
                </div>
                {this.props.readOnly ? (
                  <div className='mb-3'>{this.state.data[field.key]}</div>
                ) : field.options ? (
                  <div className='full-width mb-2'>
                    <Select
                      onChange={(v) => {
                        this.update(field.key, v.value)
                      }}
                      options={field.options}
                      value={
                        this.state.data[field.key] &&
                        field.options.find(
                          (v) => v.value === this.state.data[field.key],
                        )
                          ? {
                              label: field.options.find(
                                (v) => v.value === this.state.data[field.key],
                              ).label,
                              value: this.state.data[field.key],
                            }
                          : {
                              label: 'Please select',
                            }
                      }
                    />
                  </div>
                ) : (
                  <Input
                    id={field.label.replace(/ /g, '')}
                    ref={(e) => (this.input = e)}
                    value={this.state.data[field.key]}
                    onChange={(e) => this.update(field.key, e)}
                    isValid={!!this.state.data[field.key]}
                    type='text'
                    className='full-width mb-2'
                  />
                )}
              </>
            ))}
          {this.state.authorised && this.props.id === 'slack' && (
            <div>
              Can't see your channel? Enter your channel ID here (C0xxxxxx)
              <Input
                ref={(e) => (this.input = e)}
                value={this.state.data.channel_id}
                onChange={(e) => this.update('channel_id', e)}
                isValid={!!this.state.data.channel_id}
                type='text'
                className='full-width mt-2'
              />
            </div>
          )}
          <ErrorMessage error={this.state.error} />
        </div>

        {!this.props.readOnly && (
          <div className={'text-right mt-2'}>
            {!!this.props.modal && (
              <Button onClick={closeModal} className='mr-2' theme='secondary'>
                Cancel
              </Button>
            )}
            <Button
              disabled={
                this.state.isLoading ||
                (!this.state.data.flagsmithEnvironment &&
                  this.props.integration.perEnvironment)
              }
              type='submit'
            >
              {this.props.integration.isOauth && !this.state.authorised
                ? 'Authorise'
                : 'Save'}
            </Button>
          </div>
        )}
      </form>
    )
  }
}

CreateEditIntegration.propTypes = {}

module.exports = CreateEditIntegration
