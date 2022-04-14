import { Component } from 'react';
import OrganisationStore from '../stores/organisation-store';
import AccountStore from '../stores/account-store';

const OrganisationProvider = class extends Component {
    static displayName = 'OrganisationProvider'

    constructor(props, context) {
        super(props, context);
        this.state = {
            isLoading: OrganisationStore.isLoading,
            projects: OrganisationStore.getProjects(),
            project: OrganisationStore.getProject(),
            users: OrganisationStore.getUsers(),
            invites: OrganisationStore.getInvites(),
            name: AccountStore.getOrganisation() && AccountStore.getOrganisation().name,
            usage: OrganisationStore.getUsage(),
        };
        ES6Component(this);
        this.listenTo(OrganisationStore, 'change', () => {
            this.setState({
                isSaving: OrganisationStore.isSaving,
                isLoading: OrganisationStore.isLoading,
                projects: OrganisationStore.getProjects(this.props.id),
                project: OrganisationStore.getProject(),
                users: OrganisationStore.getUsers(),
                invites: OrganisationStore.getInvites(),
                inviteLinks: OrganisationStore.getInviteLinks(),
                usage: OrganisationStore.getUsage(),
                influx_data: OrganisationStore.getInflux(),
            });
        });
        this.listenTo(OrganisationStore, 'saved', () => {
            this.props.onSave && this.props.onSave(OrganisationStore.savedId);
        });
    }

    createProject = (name) => {
        AppActions.createProject(name);
    };

    selectProject = (id) => {
        AppActions.getProject(id);
    };

    render() {
        return (
            this.props.children(
                {
                    ...{
                        isSaving: OrganisationStore.isSaving,
                        isLoading: OrganisationStore.isLoading,
                        projects: OrganisationStore.getProjects(this.props.id),
                        project: OrganisationStore.getProject(),
                        users: OrganisationStore.getUsers(),
                        invites: OrganisationStore.getInvites(),
                        inviteLinks: OrganisationStore.getInviteLinks(),
                        usage: OrganisationStore.getUsage(),
                        influx_data: OrganisationStore.getInflux(),
                    },
                    createProject: this.createProject,
                    selectProject: this.selectProject,
                },
            )
        );
    }
};

OrganisationProvider.propTypes = {};

module.exports = OrganisationProvider;
