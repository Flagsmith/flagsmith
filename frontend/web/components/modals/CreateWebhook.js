import React, { Component } from 'react'
import Constants from 'common/constants'
import ConfigProvider from 'common/providers/ConfigProvider'
import Highlight from 'components/Highlight'
import ErrorMessage from 'components/ErrorMessage'
import TestWebhook from 'components/TestWebhook'
import ViewDocs from 'components/ViewDocs'

const exampleJSON = Constants.exampleWebhook

const CreateWebhook = class extends Component {
  static displayName = 'CreateWebhook'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = {
      enabled: this.props.isEdit ? this.props.webhook.enabled : true,
      error: false,
      secret: this.props.isEdit ? this.props.webhook.secret : '',
      url: this.props.isEdit ? this.props.webhook.url : '',
    }
  }

  save = () => {
    const webhook = {
      enabled: this.state.enabled,
      secret: this.state.secret,
      url: this.state.url,
    }
    if (this.props.isEdit) {
      webhook.id = this.props.webhook.id
    }
    this.setState({ error: false, isSaving: true })
    this.props
      .save(webhook)
      .then(() => closeModal())
      .catch(() => {
        this.setState({ error: true, isSaving: false })
      })
  }

  render() {
    const {
      props: { isEdit },
      state: { enabled, error, isSaving, url },
    } = this
    return (
      <div className='px-4'>
        <ProjectProvider id={this.props.projectId}>
          {({ project }) => (
            <form
              className='mt-4'
              onSubmit={(e) => {
                e.preventDefault()
                this.save()
              }}
            >
              <Row space>
                <Flex className='mb-4'>
                  <div>
                    <label>*URL (Expects a 200 response from POST)</label>
                  </div>
                  <Input
                    ref={(e) => (this.input = e)}
                    value={this.state.url}
                    onChange={(e) =>
                      this.setState({ url: Utils.safeParseEventValue(e) })
                    }
                    isValid={url && url.length}
                    type='text'
                    inputClassName='input--wide'
                    placeholder='https://example.com/feature-changed/'
                  />
                </Flex>
                <Row className='ms-4'>
                  <Switch
                    defaultChecked={enabled}
                    checked={enabled}
                    onChange={(enabled) => this.setState({ enabled })}
                  />
                  <span
                    onClick={() => this.setState({ enabled: !enabled })}
                    className='ms-2'
                  >
                    {' '}
                    Enable
                  </span>
                </Row>
              </Row>
              <Flex className='mb-4'>
                <div>
                  <label>
                    Secret (Optional) -{' '}
                    <a
                      className='text-info'
                      target='_blank'
                      href='https://docs.flagsmith.com/system-administration/webhooks#audit-log-web-hooks'
                      rel='noreferrer'
                    >
                      More info
                    </a>{' '}
                  </label>
                </div>
                <Input
                  ref={(e) => (this.input = e)}
                  value={this.state.secret}
                  onChange={(e) =>
                    this.setState({ secret: Utils.safeParseEventValue(e) })
                  }
                  isValid={url && url.length}
                  type='text'
                  className='full-width'
                  placeholder='Secret'
                />
              </Flex>
              <Flex className='mb-4'>
                {error && (
                  <ErrorMessage error='Could not create a webhook for this url, please ensure you include http or https.' />
                )}
                <div className={isEdit ? 'footer' : ''}>
                  <div className='mb-3'>
                    <p className='text-dark fw-bold'>
                      This will {isEdit ? 'update' : 'create'} a webhook for the
                      environment{' '}
                      <strong>
                        {
                          _.find(project.environments, {
                            api_key: this.props.environmentId,
                          }).name
                        }
                      </strong>
                    </p>
                  </div>
                  <div className='justify-content-end flex-row'>
                    <TestWebhook
                      json={Constants.exampleWebhook}
                      webhook={this.state.url}
                      secret={this.state.secret}
                    />
                    {isEdit ? (
                      <Button
                        className='ml-3'
                        data-test='update-feature-btn'
                        id='update-feature-btn'
                        disabled={isSaving || !url}
                        type='submit'
                      >
                        {isSaving ? 'Updating' : 'Update Webhook'}
                      </Button>
                    ) : (
                      <Button
                        className='ml-3'
                        type='submit'
                        disabled={isSaving || !url}
                      >
                        {isSaving ? 'Creating' : 'Create Webhook'}
                      </Button>
                    )}
                  </div>
                </div>
              </Flex>
              <FormGroup className='ml-1'>
                <div>
                  <Row className='mb-3' space>
                    <div className='font-weight-medium text-dark'>
                      Example Payload
                    </div>
                    <ViewDocs href='https://docs.flagsmith.com/system-administration/webhooks#environment-web-hooks' />
                  </Row>

                  <Highlight
                    forceExpanded
                    style={{ marginBottom: 10 }}
                    className='json'
                  >
                    {exampleJSON}
                  </Highlight>
                </div>
              </FormGroup>
            </form>
          )}
        </ProjectProvider>
      </div>
    )
  }
}

CreateWebhook.propTypes = {}

module.exports = ConfigProvider(CreateWebhook)
