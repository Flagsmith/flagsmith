import React, { Component } from 'react';
import IdentitySegmentsStore from '../stores/identity-segments-store';

const IdentitySegmentsProvider = class extends Component {
    static displayName = 'IdentitySegmentsProvider'

    constructor(props, context) {
        super(props, context);
        this.state = {
            isLoading: IdentitySegmentsStore.isLoading,
            segments: IdentitySegmentsStore.model[props.id],
            segmentsPaging: IdentitySegmentsStore.paging,
        };
        ES6Component(this);
    }

    componentDidMount() {
        if (this.props.fetch && !this.state.segments) {
            AppActions.getIdentitySegments(this.props.projectId, this.props.id)
        }
        this.listenTo(IdentitySegmentsStore, 'change', () => {
            this.setState({
                isLoading: IdentitySegmentsStore.isLoading,
                segments: IdentitySegmentsStore.model[this.props.id],
                segmentsPaging: IdentitySegmentsStore.paging,
            });
        });
    }

    render() {
        return (
            this.props.children({ ...this.state }, { })
        );
    }
};

IdentitySegmentsProvider.propTypes = {};

module.exports = IdentitySegmentsProvider;
