import React, { Component } from 'react';
import FeatureListStore from '../stores/feature-list-store';
import IdentityStore from '../stores/identity-store';

const IdentityProvider = class extends Component {
    static displayName = 'IdentityProvider'

    constructor(props, context) {
        super(props, context);
        this.state = {
            isLoading: true,
            identity: IdentityStore.model,
            environmentFlags: FeatureListStore.getEnvironmentFlags(),
            projectFlags: FeatureListStore.getProjectFlags(),
            identityFlags: IdentityStore.getIdentityFlags(),
        };
        ES6Component(this);
    }

    componentDidMount() {
        this.listenTo(IdentityStore, 'change', () => {
            this.setState({
                isSaving: IdentityStore.isSaving,
                isLoading: IdentityStore.isLoading || FeatureListStore.isLoading,
                identity: IdentityStore.model,
                identityFlags: IdentityStore.getIdentityFlags(),
                traits: IdentityStore.getTraits(),
            });
        });
        this.listenTo(FeatureListStore, 'change', () => {
            this.setState({
                isLoading: IdentityStore.isLoading || FeatureListStore.isLoading,
                environmentFlags: FeatureListStore.getEnvironmentFlags(),
                projectFlags: FeatureListStore.getProjectFlags(),
            });
        });

        this.listenTo(IdentityStore, 'saved', () => {
            this.props.onSave && this.props.onSave();
        });
    }

    toggleFlag = ({ identity, projectFlag, environmentFlag, identityFlag, environmentId }) => {
        AppActions.toggleUserFlag({ identity, projectFlag, environmentFlag, identityFlag, environmentId });
    };

    editFlagValue = ({ identity, projectFlag, environmentFlag, identityFlag, environmentId }) => {
        AppActions.editUserFlag({ identity, projectFlag, environmentFlag, identityFlag, environmentId });
    };

    editTrait = ({ trait, identity, environmentId }) => {
        AppActions.editTrait({ trait, identity, environmentId });
    };

    removeFlag = ({ environmentId, identity, identityFlag }) => {
        AppActions.removeUserFlag({ environmentId, identity, identityFlag });
    };

    changeUserFlag = ({identity, identityFlag, environmentId, payload}) => {
        AppActions.changeUserFlag({identity, identityFlag, environmentId, payload});
    };

    render() {
        const { toggleFlag, editFlagValue, removeFlag, editTrait, changeUserFlag } = this;
        return (
            this.props.children({ ...this.state }, { toggleFlag, editFlagValue, removeFlag, editTrait, changeUserFlag })
        );
    }
};

IdentityProvider.propTypes = {};

module.exports = IdentityProvider;
