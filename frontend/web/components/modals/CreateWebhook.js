import React, { Component } from 'react'
import Constants from 'common/constants'
import ConfigProvider from 'common/providers/ConfigProvider'
import Highlight from 'components/Highlight'
import ErrorMessage from 'components/ErrorMessage'
import TestWebhook from 'components/TestWebhook'

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
      <ProjectProvider id={this.props.projectId}>
        {({ project }) => (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              this.save()
            }}
          >
            <Row space>
              <Flex className='mb-4 mr-4'>
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
              <FormGroup className='mb-4 ml-1'>
                <div>
                  <label>Enabled</label>
                </div>
                <div>
                  <Switch
                    defaultChecked={enabled}
                    checked={enabled}
                    onChange={(enabled) => this.setState({ enabled })}
                  />
                </div>
              </FormGroup>
            </Row>
            <Flex className='mb-4 mr-4'>
              <div>
                <label>
                  Secret (Optional) -{' '}
                  <a
                    className='text-info'
                    target='_blank'
                    href='https://docs.flagsmith.com/advanced-use/system-administration#validating-signature'
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
                inputClassName='input--wide'
                placeholder='Secret'
              />
            </Flex>
            <Flex className='mb-4 mr-4'>
              {error && (
                <ErrorMessage error='Could not create a webhook for this url, please ensure you include http or https.' />
              )}
              <div className={isEdit ? 'footer' : ''}>
                <div className='mb-3'>
                  <p className='text-right'>
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
                <div className='text-right'>
                  <p>
                    <TestWebhook
                      json={Constants.exampleWebhook}
                      webhook={this.state.url}
                    />
                  </p>
                </div>
                <div className='text-right'>
                  {isEdit ? (
                    <Button
                      data-test='update-feature-btn'
                      id='update-feature-btn'
                      disabled={isSaving || !url}
                    >
                      {isSaving ? 'Creating' : 'Update Webhook'}
                    </Button>
                  ) : (
                    <Button
                      data-test='create-feature-btn'
                      id='create-feature-btn'
                      disabled={isSaving || !url}
                    >
                      {isSaving ? 'Creating' : 'Create Webhook'}
                    </Button>
                  )}
                </div>
              </div>
            </Flex>
            <FormGroup className='mb-4 ml-1'>
              <div>
                <label>Example Payload </label>
                <Button
                  theme='text'
                  className='ml-1'
                  href='https://docs.flagsmith.com/advanced-use/system-administration'
                  target='_blank'
                >
                  View docs
                </Button>
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
    )
  }
}

CreateWebhook.propTypes = {}

module.exports = ConfigProvider(CreateWebhook)
