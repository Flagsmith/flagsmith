// import propTypes from 'prop-types';
import React, { Component } from 'react';
import EnvironmentSelect from '../EnvironmentSelect';

class TheComponent extends Component {
    static displayName = 'TheComponent';

    static propTypes = {};

    constructor(props) {
        super();
        this.state = {
            environmentLeft: props.match.params.environmentId,
            environmentRight: '',
            isLoading: true,
        };
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        if (this.state.environmentLeft !== prevState.environmentLeft || this.state.environmentRight !== prevState.environmentRight) {
            this.setState({ isLoading: true });
        }
    }

    render() {
        return (
            <div className="app-container container">
                <h3>
                    Compare Environments
                </h3>
                <p>
                    Compare feature flag and segment override changes across environments.
                </p>
                <Row>
                    <Row>
                        <div style={{ width: 200 }}>
                            <EnvironmentSelect onChange={environmentLeft => this.setState({ environmentLeft })} value={this.state.environmentLeft}/>
                        </div>

                        <div>
                            <ion className="icon ios ion-md-arrow-back mx-2"/>
                        </div>

                        <div style={{ width: 200 }}>
                            <EnvironmentSelect ignoreAPIKey={this.state.environmentLeft} onChange={environmentRight => this.setState({ environmentRight })} value={this.state.environmentRight}/>
                        </div>
                    </Row>

                </Row>

                {
                    this.state.environmentLeft && this.state.environmentRight ? (
                        <div className="centered-container">
                            {this.state.isLoading && (
                                <Loader/>
                            )}
                        </div>
                    ) : ''
                }

            </div>
        );
    }
}

export default ConfigProvider(TheComponent);
