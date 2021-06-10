import React, { Component } from 'react';
import PermissionsStore from '../stores/permissions-store';

const AvailablePermissionsProvider = class extends Component {
    static displayName = 'AvailablePermissionsProvider'

    constructor(props, context) {
        super(props, context);
        this.state = {
            isLoading: PermissionsStore.isLoading,
            permissions: PermissionsStore.getAvailablePermissions(props.level),
        };
        ES6Component(this);
    }

    componentDidMount = () => {
        this.listenTo(PermissionsStore, 'change', () => {
            this.setState({
                isLoading: PermissionsStore.isLoading,
                permissions: PermissionsStore.getAvailablePermissions(this.props.level),
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

AvailablePermissionsProvider.propTypes = {};

module.exports = AvailablePermissionsProvider;
