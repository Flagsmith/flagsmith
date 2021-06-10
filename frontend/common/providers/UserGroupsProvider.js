import React, { Component } from 'react';
import UserGroupsStore from '../stores/user-group-store';

const UserGroupProvider = class extends Component {
    static displayName = 'UserGroupProvider'

    constructor(props, context) {
        super(props, context);
        this.state = {
            isLoading: !UserGroupsStore.model,
            userGroups: UserGroupsStore.model,
            userGroupsPaging: UserGroupsStore.paging,
        };
        ES6Component(this);
    }

    componentDidMount() {
        this.listenTo(UserGroupsStore, 'change', () => {
            this.setState({
                isSaving: UserGroupsStore.isSaving,
                isLoading: UserGroupsStore.isLoading,
                userGroups: UserGroupsStore.model,
                userGroupsPaging: UserGroupsStore.paging,
            });
        });

        this.listenTo(UserGroupsStore, 'saved', () => {
            this.props.onSave && this.props.onSave();
        });
    }

    render() {
        return (
            this.props.children({ ...this.state })
        );
    }
};

UserGroupProvider.propTypes = {};

module.exports = UserGroupProvider;
