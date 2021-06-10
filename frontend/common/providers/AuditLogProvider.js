import React, { Component } from 'react';
import AuditLogStore from '../stores/audit-log-store';

const AuditLogProvider = class extends Component {
    static displayName = 'AuditLogProvider'

    constructor(props, context) {
        super(props, context);
        this.state = {
            isLoading: !AuditLogStore.model,
            auditLog: AuditLogStore.model,
            auditLogPaging: AuditLogStore.paging,
        };
        ES6Component(this);
    }

    componentDidMount() {
        this.listenTo(AuditLogStore, 'change', () => {
            this.setState({
                isSaving: AuditLogStore.isSaving,
                isLoading: AuditLogStore.isLoading,
                auditLog: AuditLogStore.model,
                auditLogPaging: AuditLogStore.paging,
            });
        });
    }

    render() {
        return (
            this.props.children({ ...this.state })
        );
    }
};

AuditLogProvider.propTypes = {};

module.exports = AuditLogProvider;
