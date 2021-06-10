import React, { Component } from 'react';
import IdentityStore from '../stores/identity-list-store';

const IdentityListProvider = class extends Component {
    static displayName = 'IdentityListProvider'

    constructor(props, context) {
        super(props, context);
        this.state = {
            isLoading: !IdentityStore.model,
            identities: IdentityStore.model,
            identitiesPaging: IdentityStore.paging,
        };
        ES6Component(this);
    }

    componentDidMount() {
        this.listenTo(IdentityStore, 'change', () => {
            this.setState({
                isSaving: IdentityStore.isSaving,
                isLoading: IdentityStore.isLoading,
                identities: IdentityStore.model,
                identitiesPaging: IdentityStore.paging,
            });
        });

        this.listenTo(IdentityStore, 'saved', () => {
            this.props.onSave && this.props.onSave();
        });
    }

    render() {
        return (
            this.props.children({ ...this.state })
        );
    }
};

IdentityListProvider.propTypes = {};

module.exports = IdentityListProvider;
