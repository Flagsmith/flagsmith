import React, { Component } from 'react';
import ConfirmRemoveEnvironment from '../modals/ConfirmRemoveEnvironment';
import ProjectStore from '../../../common/stores/project-store';
import ConfigProvider from '../../../common/providers/ConfigProvider';
import withWebhooks from '../../../common/providers/withWebhooks';
import CreateWebhookModal from '../modals/CreateWebhook';
import ConfirmRemoveWebhook from '../modals/ConfirmRemoveWebhook';
import EditPermissions from '../EditPermissions';
import ServerSideSDKKeys from "../ServerSideSDKKeys";
import PaymentModal from "../modals/Payment";

const EnvironmentSettingsPage = class extends Component {
    static displayName = 'EnvironmentSettingsPage'

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props, context) {
        super(props, context);
        this.state = {};
        AppActions.getProject(this.props.match.params.projectId);
    }

    componentDidMount = () => {
        API.trackPage(Constants.pages.ENVIRONMENT_SETTINGS);
        this.props.getWebhooks();
    };

    onSave = () => {
        toast('Environment Saved');
    };

    componentWillReceiveProps(newProps) {
        if (newProps.projectId !== this.props.projectId) {
            AppActions.getProject(newProps.match.params.projectId);
        }
    }

    onRemove = () => {
        toast('Your project has been removed');
        this.context.router.history.replace('/projects');
    };

    confirmRemove = (environment, cb) => {
        openModal('Remove Environment', <ConfirmRemoveEnvironment
            environment={environment}
            cb={cb}
        />);
    };

    onRemoveEnvironment = () => {
        const envs = ProjectStore.getEnvs();
        if (envs && envs.length) {
            this.context.router.history.replace(`/project/${this.props.match.params.projectId}/environment` + `/${envs[0].api_key}/features`);
        } else {
            this.context.router.history.replace(`/project/${this.props.match.params.projectId}/environment/create`);
        }
    };

    saveEnv = (e) => {
        e && e.preventDefault();
        const { name } = this.state;
        if (ProjectStore.isSaving || (!name)) {
            return;
        }
        const env = _.find(ProjectStore.getEnvs(), { api_key: this.props.match.params.environmentId });
        AppActions.editEnv(Object.assign({}, env, {
            name: name || env.name,
            minimum_change_request_approvals: this.state.minimum_change_request_approvals,
        }));
    }

    saveDisabled = () => {
        const { name } = this.state;
        if (ProjectStore.isSaving || (!name)) {
            return true;
        }

        const env = _.find(ProjectStore.getEnvs(), { api_key: this.props.match.params.environmentId });

        // Must have name
        if (name !== undefined && !name) {
            return true;
        }

        return false;
    }

    createWebhook = () => {
        openModal('New Webhook', <CreateWebhookModal
            router={this.context.router}
            environmentId={this.props.match.params.environmentId}
            projectId={this.props.match.params.projectId}
            save={this.props.createWebhook}
        />, null, { className: 'alert fade expand' });
    };


    editWebhook = (webhook) => {
        openModal('Edit Webhook', <CreateWebhookModal
            router={this.context.router}
            webhook={webhook}
            isEdit
            environmentId={this.props.match.params.environmentId}
            projectId={this.props.match.params.projectId}
            save={this.props.saveWebhook}
        />, null, { className: 'alert fade expand' });
    };

    deleteWebhook = (webhook) => {
        openModal('Remove Webhook', <ConfirmRemoveWebhook
            environmentId={this.props.match.params.environmentId}
            projectId={this.props.match.params.projectId}
            url={webhook.url}
            cb={() => this.props.deleteWebhook(webhook)}
        />);
    };

    render() {
        const { props: { webhooks, webhooksLoading }, state: { name } } = this;
        const has4EyesPermission = Utils.getPlansPermission('4_EYES');

        return (
            <div className="app-container container">
                <ProjectProvider
                    onRemoveEnvironment={this.onRemoveEnvironment}
                    id={this.props.match.params.projectId} onRemove={this.onRemove} onSave={this.onSave}
                >
                    {({ isLoading, isSaving, editProject, editEnv, deleteProject, deleteEnv, project }) => {
                        const env = _.find(project.environments, { api_key: this.props.match.params.environmentId });
                        if (env && (typeof this.state.minimum_change_request_approvals !== "number")) {
                            setTimeout(()=>{
                                this.setState({
                                    name:env.name,
                                    minimum_change_request_approvals:env.minimum_change_request_approvals,
                                })
                            },10)
                        }
                        return (
                            <div>
                                {isLoading && <div className="centered-container"><Loader/></div>}
                                {!isLoading && (
                                    <div>
                                        <div className="panel--grey">
                                            <FormGroup>
                                                <h3>Environment Name</h3>
                                                <form onSubmit={this.saveEnv}>
                                                    <Row>
                                                        <Column className="m-l-0">
                                                            <Input
                                                                ref={e => this.input = e}
                                                                value={typeof this.state.name == "string" ? this.state.name : env.name}
                                                                inputClassName="input input--wide"
                                                                name="env-name"

                                                                onChange={e => this.setState({ name: Utils.safeParseEventValue(e) })}
                                                                isValid={name && name.length}
                                                                type="text" title={<h3>Environment Name</h3>}
                                                                placeholder="Environment Name"
                                                            />
                                                        </Column>
                                                        <Button
                                                            id="save-env-btn" className="float-right"
                                                            disabled={this.saveDisabled()}
                                                        >
                                                            {isSaving ? 'Updating' : 'Update Name'}
                                                        </Button>
                                                    </Row>
                                                </form>
                                            </FormGroup>
                                            <FormGroup className="m-t-1">
                                                <label className="m-b-0">Client Side Environment Key</label>
                                                <Row>
                                                    <Input
                                                        value={this.props.match.params.environmentId}
                                                        inputClassName="input input--wide"
                                                        type="text" title={<h3>Client Side Environment Key</h3>}
                                                        placeholder="Client Side Environment Key"
                                                    />
                                                </Row>
                                            </FormGroup>
                                        </div>
                                        {this.props.hasFeature("serverside_sdk_keys") && (
                                            <ServerSideSDKKeys environmentId={this.props.match.params.environmentId}/>
                                        )}

                                        <FormGroup className="mt-1">
                                            <EditPermissions
                                                tabClassName="flat-panel"
                                                parentId={this.props.match.params.projectId}
                                                parentLevel="project"
                                                parentSettingsLink={`/project/${this.props.match.params.projectId}/settings`}
                                                id={this.props.match.params.environmentId}
                                                level="environment"
                                            />
                                        </FormGroup>
                                        {this.props.hasFeature("4eyes") && (

                                            <FormGroup className="m-y-3">
                                                <Row space>
                                                    <div className="col-md-8 pl-0">
                                                        <h3 className="m-b-0">Change Requests</h3>
                                                        {!has4EyesPermission? (
                                                            <p>
                                                                View and manage your feature changes with a Change Request flow with our <a
                                                                href="#" onClick={() => {
                                                                openModal('Payment plans', <PaymentModal
                                                                    viewOnly={false}
                                                                />, null, { large: true });
                                                            }}
                                                            >Scaleup plan
                                                            </a>. Find out more <a href="https://docs.flagsmith.com/advanced-use/change-requests" target="_blank">here</a>.
                                                            </p>
                                                        ): (
                                                            <p>
                                                                Require a minimum number of people to approve changes to features.
                                                                {' '}
                                                                <ButtonLink
                                                                    href="https://docs.flagsmith.com/advanced-use/change-requests"
                                                                    target="_blank"
                                                                >Learn about Change Requests.</ButtonLink>
                                                            </p>
                                                        )}

                                                    </div>
                                                    <div className="col-md-4 pr-0 text-right">
                                                            <div>
                                                                <Switch disabled={!has4EyesPermission} className="float-right" checked={has4EyesPermission && Utils.changeRequestsEnabled(this.state.minimum_change_request_approvals)} onChange={(v)=>this.setState({minimum_change_request_approvals: v?0:null}, this.saveEnv)} />
                                                            </div>
                                                    </div>
                                                </Row>
                                                {Utils.changeRequestsEnabled(this.state.minimum_change_request_approvals) && has4EyesPermission&& (
                                                    <div>
                                                        <div className="mb-2">
                                                            <strong>Minimum number of approvals</strong>

                                                        </div>
                                                        <Row>
                                                            <Column className="m-l-0">
                                                                <Input
                                                                    ref={e => this.input = e}
                                                                    value={`${this.state.minimum_change_request_approvals}`}
                                                                    inputClassName="input input--wide"
                                                                    name="env-name"
                                                                    style={{minWidth:50}}
                                                                    onChange={e => {
                                                                        if(!Utils.safeParseEventValue(e)) return
                                                                        this.setState({
                                                                            minimum_change_request_approvals: parseInt(Utils.safeParseEventValue(e))
                                                                        })
                                                                    }}
                                                                    isValid={name && name.length}
                                                                    type="number"
                                                                    placeholder="Minimum number of approvals"
                                                                />
                                                            </Column>
                                                            <Button
                                                                type="button"
                                                                onClick={this.saveEnv}
                                                                id="save-env-btn" className="float-right"
                                                                disabled={this.saveDisabled()||isSaving||isLoading}
                                                            >
                                                                {isSaving || isLoading ? 'Saving' : 'Save'}
                                                            </Button>
                                                        </Row>
                                                    </div>
                                                )}
                                            </FormGroup>
                                        )}
                                        <FormGroup className="m-y-3">
                                            <Row className="mb-3" space>
                                                <div className="col-md-8 pl-0">
                                                    <h3 className="m-b-0">Feature Webhooks</h3>
                                                    <p>
                                                        Feature webhooks let you know when features have changed. You
                                                        can configure 1 or more Feature Webhooks per Environment.
                                                        {' '}
                                                        <ButtonLink
                                                            href="https://docs.flagsmith.com/advanced-use/system-administration#web-hooks"
                                                            target="_blank"
                                                        >Learn about Feature Webhooks.</ButtonLink>
                                                    </p>
                                                </div>
                                                <div className="col-md-4 pr-0">
                                                    <Button className="float-right" onClick={this.createWebhook}>
                                                        Create feature webhook
                                                    </Button>
                                                </div>
                                            </Row>
                                            {webhooksLoading && !webhooks ? (
                                                <Loader/>
                                            ) : (
                                                <PanelSearch
                                                    id="webhook-list"
                                                    title={(
                                                        <Tooltip
                                                            title={<h6 className="mb-0">Webhooks <span
                                                                className="icon ion-ios-information-circle"
                                                            /></h6>}
                                                            place="right"
                                                        >
                                                            {Constants.strings.WEBHOOKS_DESCRIPTION}
                                                        </Tooltip>
                                                    )}
                                                    className="no-pad"
                                                    icon="ion-md-cloud"
                                                    items={webhooks}
                                                    renderRow={webhook => (
                                                        <Row
                                                            onClick={() => {
                                                                this.editWebhook(webhook);
                                                            }} space className="list-item clickable cursor-pointer"
                                                            key={webhook.id}
                                                        >
                                                            <div>
                                                                <ButtonLink>
                                                                    {webhook.url}
                                                                </ButtonLink>
                                                                <div className="list-item-footer faint">
                                                                    Created
                                                                    {' '}
                                                                    {moment(webhook.created_date).format('DD/MMM/YYYY')}
                                                                </div>
                                                            </div>
                                                            <Row>
                                                                <Switch checked={webhook.enabled}/>
                                                                <button
                                                                    id="delete-invite"
                                                                    type="button"
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        e.preventDefault();
                                                                        this.deleteWebhook(webhook);
                                                                    }}
                                                                    className="btn btn--with-icon ml-auto btn--remove"
                                                                >
                                                                    <RemoveIcon/>
                                                                </button>
                                                            </Row>
                                                        </Row>
                                                    )}
                                                    renderNoResults={(
                                                        <Panel
                                                            id="users-list"
                                                            icon="ion-md-cloud"
                                                            title={(
                                                                <Tooltip
                                                                    title={<h6 className="mb-0">Webhooks <span
                                                                        className="icon ion-ios-information-circle"
                                                                    /></h6>}
                                                                    place="right"
                                                                >
                                                                    {Constants.strings.WEBHOOKS_DESCRIPTION}
                                                                </Tooltip>
                                                            )}
                                                        >
                                                            You currently have no Feature Webhooks configured for this
                                                            Environment.
                                                        </Panel>
                                                    )}
                                                    isLoading={this.props.webhookLoading}
                                                />
                                            )}
                                        </FormGroup>

                                        <FormGroup className="m-y-3">
                                            <Row>
                                                <Column className="d-flex">
                                                    <h3>
                                                        Delete Environment
                                                    </h3>
                                                    <p>
                                                        This environment will be permanently deleted.
                                                    </p>
                                                </Column>
                                                <Button
                                                    id="delete-env-btn"
                                                    onClick={() => this.confirmRemove(_.find(project.environments, { api_key: this.props.match.params.environmentId }), () => {
                                                        deleteEnv(_.find(project.environments, { api_key: this.props.match.params.environmentId }));
                                                    })}
                                                    className="btn btn--with-icon ml-auto btn--remove"
                                                >
                                                    <RemoveIcon/>
                                                </Button>
                                            </Row>
                                        </FormGroup>
                                    </div>

                                )}
                            </div>
                        );
                    }}
                </ProjectProvider>
            </div>
        );
    }
};

EnvironmentSettingsPage.propTypes = {};

module.exports = ConfigProvider(withWebhooks(EnvironmentSettingsPage));
