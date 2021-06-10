import React, { Component } from 'react';


const DemoPage = class extends Component {
    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    static displayName = 'DemoPage'

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    componentDidMount = () => {
        setTimeout(() => {
            AppActions.login(Project.demoAccount);
        }, 2000);
    };


    render() {
        return (
            <div className="app-container animated fadeIn">
                <AccountProvider onSave={this.onSave}>
                    {({ isSaving, error }) => (
                        <div className="centered-container">
                            <div>
                                {error ? (
                                    <div>
                                        <h3>
                                            Oops
                                        </h3>
                                        <p>
                                            We could not login to the demo account please contact
                                            {' '}
                                            <a
                                              href="support@bullet-train.io"
                                            >
                                                Support
                                            </a>
                                        </p>
                                    </div>
                                ) : (
                                    <div className="text-center">
                                        <Loader/>
                                        <p className="faint-lg">
                                            Signing you into the demo account
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </AccountProvider>
            </div>
        );
    }
};

DemoPage.propTypes = {};

module.exports = DemoPage;
