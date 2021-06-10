import React, { Component } from 'react';
import ProjectStore from '../stores/project-store';
import EnvironmentStore from '../stores/environment-store';
import OrganisationStore from '../stores/organisation-store';

export default (WrappedComponent) => {
    class HOC extends React.Component {
        static displayName = 'withPrescriptionHistory';

        constructor(props, context) {
            super(props, context);
            this.state = this.getSelection();
            ES6Component(this);
            this.listenTo(ProjectStore, 'loaded', this.setNav);
            // this.listenTo(EnvironmentStore, 'loaded', this.setNav)
            this.listenTo(OrganisationStore, 'loaded', this.setNav);
            this.listenTo(EnvironmentStore, 'selected', this.setNav);
        }

        setNav = () => {
            const selection = this.getSelection();
            const before = JSON.stringify(this.state);
            const after = JSON.stringify(selection);
            if (before !== after) {
                this.setState(selection);
            }
        }

        getSelection = () => {
            const {
                orgId,
                projectId,
                environmentId,
            } = EnvironmentStore.getSelection();
            const selectedOrganisation = AccountStore.getOrganisation();
            const selectedEnvironment = ProjectStore.getEnvironment(environmentId);
            const selectedProject = OrganisationStore.getProject(projectId);
            return {
                orgId,
                projectId,
                environmentId,
                selectedProject,
                selectedEnvironment,
                selectedOrganisation,
                selectionLoaded: !!(selectedProject && selectedEnvironment && selectedOrganisation),
            };
        };

        render() {
            return (
                <WrappedComponent
                  ref={c => this.wrappedComponent = c}
                  {...this.state}
                  {...this.props}
                />
            );
        }
    }

    return HOC;
};
