import React, { Component } from 'react';
import Highlight from '../Highlight';
import ErrorMessage from '../ErrorMessage';
import Constants from '../../../common/constants';
import TestWebhook from '../TestWebhook';

const exampleJSON = Constants.exampleAuditWebhook;

const CreateAuditWebhook = class extends Component {
  static displayName = 'CreateAuditWebhook';

  static contextTypes = {
      router: propTypes.object.isRequired,
  };

  constructor(props, context) {
      super(props, context);
      this.state = {
          enabled: this.props.isEdit ? this.props.webhook.enabled : true,
          url: this.props.isEdit ? this.props.webhook.url : '',
          error: false,
      };
  }

  save = () => {
      const webhook = {
          url: this.state.url,
          enabled: this.state.enabled,
      };
      if (this.props.isEdit) {
          webhook.id = this.props.webhook.id;
      }
      this.setState({ isSaving: true, error: false });
      this.props.save(webhook)
          .then(() => closeModal())
          .catch((e) => {
              this.setState({ error: true, isSaving: false });
          });
  };

  render() {
      const { state: { error, isSaving, url, enabled }, props: { isEdit } } = this;
      return (
          <ProjectProvider
            id={this.props.projectId}
          >
              {({ project }) => (

                  <form
                    id="create-feature-modal"
                    onSubmit={(e) => {
                        e.preventDefault();
                        this.save();
                    }}
                  >
                      <Row space>
                          <Flex className="mb-4 mr-4">
                              <div>
                                  <label>URL (Expects a 200 response from POST)</label>
                              </div>
                              <Input
                                ref={e => this.input = e}
                                value={this.state.url}
                                onChange={e => this.setState({ url: Utils.safeParseEventValue(e) })}
                                isValid={url && url.length}
                                type="text"
                                inputClassName="input--wide"
                                placeholder="https://example.com/audit/"
                              />
                          </Flex>
                          <FormGroup className="mb-4 ml-1">
                              <div>
                                  <label>Enabled</label>
                              </div>
                              <div>
                                  <Switch
                                    defaultChecked={enabled}
                                    checked={enabled}
                                    onChange={enabled => this.setState({ enabled })}
                                  />
                              </div>
                          </FormGroup>
                      </Row>
                      <FormGroup className="mb-4 ml-1">
                          <div>
                              <label>Example Payload </label>
                              <a className="link-dark ml-2" href="https://docs.flagsmith.com/audit-logs/" target="_blank">View docs</a>
                              <Highlight style={{ marginBottom: 10 }} className="json">
                                  {exampleJSON}
                              </Highlight>
                              <div className="text-center">
                                  <TestWebhook json={Constants.exampleAuditWebhook} webhook={this.state.url}/>
                              </div>
                          </div>
                      </FormGroup>
                      {error && <ErrorMessage error="Could not create a webhook for this url, please ensure you include http or https."/>}
                      <div className={isEdit ? 'footer' : ''}>
                          <div className="mb-3">
                              <p className="text-right">
                  This will {isEdit ? 'update' : 'create'} a webhook the organisation
                                  {' '}
                                  <strong>
                                      {AccountStore.getOrganisation().name}
                                  </strong>
                              </p>
                          </div>
                          <div className="text-right">
                              {isEdit ? (
                                  <Button
                                    className="mt-3" data-test="update-feature-btn" id="update-feature-btn"
                                    disabled={isSaving || !url}
                                  >
                                      {isSaving ? 'Creating' : 'Update Webhook'}
                                  </Button>
                              ) : (
                                  <Button
                                    className="mt-3" data-test="create-feature-btn" id="create-feature-btn"
                                    disabled={isSaving || !url}
                                  >
                                      {isSaving ? 'Creating' : 'Create Webhook'}
                                  </Button>
                              )}
                          </div>
                      </div>
                  </form>
              )}
          </ProjectProvider>
      );
  }
};

CreateAuditWebhook.propTypes = {};

module.exports = ConfigProvider(CreateAuditWebhook);
