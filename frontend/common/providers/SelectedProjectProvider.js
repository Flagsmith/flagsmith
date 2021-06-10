import React, { Component } from 'react';
import OrganisationStore from '../stores/organisation-store';

const SelectedProjectProvider = class extends Component {
    static displayName = 'SelectedProjectProvider';

    constructor(props, context) {
        super(props, context);
        this.state = {
            isLoading: !OrganisationStore.getProjects(),
            project: OrganisationStore.getProject(this.props.id),
        };
        ES6Component(this);
        this.listenTo(OrganisationStore, 'change', () => {
            this.setState({
                isLoading: !OrganisationStore.getProjects(),
                project: OrganisationStore.getProject(this.props.id),
            });
        });
    }

    render() {
        return (
            this.props.children(
                {
                    ...this.state,
                },
            )
        );
    }
};

SelectedProjectProvider.propTypes = {};

module.exports = SelectedProjectProvider;
