import React, { Component } from 'react';
import flagsmith from 'flagsmith';
import propTypes from 'prop-types';
import ConfigStore from '../stores/config-store';

module.exports = (WrappedComponent) => {
    class HOC extends Component {
        static contextTypes = {
            router: propTypes.object.isRequired,
        };
        constructor(props) {
            super(props);
            this.state = {
                isLoading: ConfigStore.model ? ConfigStore.isLoading : true,
                error: ConfigStore.error,
            };
            ES6Component(this);
        }

        componentDidMount() {
            this.listenTo(ConfigStore, 'change', () => {
                this.setState({
                    isLoading: ConfigStore.isLoading,
                    error: ConfigStore.error,
                });
            });
        }

        render() {
            const { isLoading, error } = this.state;
            const { getValue, hasFeature } = flagsmith;


            return (
                <WrappedComponent
                  ref="wrappedComponent"
                  isLoading={isLoading}
                  error={error}
                  router={this.context.router}
                  {...this.props}
                  getValue={getValue}
                  hasFeature={hasFeature}
                />
            );
        }
    }

    return HOC;
};
