import React, { Component } from 'react';
import Highlight from '../Highlight';
import ErrorMessage from '../ErrorMessage';
import Constants from 'common/constants';
import ConfigProvider from 'common/providers/ConfigProvider';
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
            secret: this.props.isEdit ? this.props.webhook.secret : '',
            url: this.props.isEdit ? this.props.webhook.url : '',
            error: false,
        };
    }

    save = () => {
        const webhook = {
            url: this.state.url,
            secret: this.state.secret,
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
                        <Flex className="mb-4 mr-4">
                            <div>
                                <label>Secret (Optional) - <a className="text-info" target="_blank" href="https://docs.flagsmith.com/advanced-use/system-administration#validating-signature">More info</a> </label>
                            </div>
                            <Input
                                ref={e => this.input = e}
                                value={this.state.secret}
                                onChange={e => this.setState({ secret: Utils.safeParseEventValue(e) })}
                                isValid={url && url.length}
                                type="text"
                                inputClassName="input--wide"
                                placeholder="Secret"
                            />
                        </Flex>
                        <Flex className="mb-4 mr-4">
                            {error && <ErrorMessage error="Could not create a webhook for this url, please ensure you include http or https." />}
                            <div className={isEdit ? 'footer' : ''}>
                                <div className="mb-3">
                                    <p className="text-right">
                                        This will {isEdit ? 'update' : 'create'} a webhook for the Organisation
                                        {' '}
                                        <strong>
                                            {AccountStore.getOrganisation().name}
                                        </strong>
                                    </p>
                                </div>
                                <div className="text-right">
                                    <TestWebhook json={Constants.exampleAuditWebhook} webhook={this.state.url} />
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
                        </Flex>
                        <FormGroup className="mb-4 ml-1">
                            <div>
                                <label>Example Payload </label>
                                <a className="link-dark ml-2" href="https://docs.flagsmith.com/advanced-use/system-administration#audit-log-webhooks" target="_blank">View docs</a>
                                <Highlight forceExpanded style={{ marginBottom: 10 }} className="json">
                                    {exampleJSON}
                                </Highlight>
                            </div>
                        </FormGroup>
                    </form>
                )}
            </ProjectProvider>
        );
    }
};

CreateAuditWebhook.propTypes = {};

module.exports = ConfigProvider(CreateAuditWebhook);
