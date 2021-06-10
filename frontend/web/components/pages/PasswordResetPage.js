import React, { Component } from 'react';


const PasswordResetPage = class extends Component {
    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    static displayName = 'PasswordResetPage'

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    componentDidMount = () => {
        API.trackPage(Constants.pages.RESET_PASSWORD);
    };

    onSave = () => {
        this.context.router.history.replace('/login');
        toast('Your password has been reset');
    }

    save = (e) => {
        e.preventDefault();
        const isValid = this.state.password && (this.state.password == this.state.password2);
        if (isValid) {
            AppActions.resetPassword({
                uid: this.props.match.params.uid,
                token: this.props.match.params.token,
                new_password1: this.state.password,
                new_password2: this.state.password2,
            });
        }
    }

    render() {
        const isValid = this.state.password && (this.state.password == this.state.password2);
        return (
            <div className="app-container">
                <AccountProvider onSave={this.onSave}>
                    {({ isSaving, error }) => (
                        <div className="card signup-form container">
                            <h3>Reset Password</h3>

                            {isSaving ? (
                                <div className="centered-container">
                                    <Loader/>
                                </div>
                            ) : (
                                <form onSubmit={this.save} id="details">
                                    <InputGroup
                                      inputProps={{
                                          name: 'new-password',
                                          className: 'full-width',
                                          error: error && error.new_password1,
                                      }}
                                      title="New Password"
                                      onChange={(e) => {
                                          this.setState({ password: Utils.safeParseEventValue(e) });
                                      }}
                                      className="input-default full-width"
                                      placeholder="New Password"
                                      type="password"
                                      name="password1" id="password1"
                                    />
                                    <InputGroup
                                      inputProps={{
                                          name: 'new-password2',
                                          className: 'full-width',
                                          error: error && error.new_password2,
                                      }}
                                      title="Confirm New Password"
                                      onChange={(e) => {
                                          this.setState({ password2: Utils.safeParseEventValue(e) });
                                      }}
                                      className="input-default full-width"
                                      placeholder="Confirm New Password"
                                      type="password"
                                      name="password2" id="password2"
                                    />
                                    <div className="text-right">
                                        <Button disabled={!isValid}>
                                            Set password
                                        </Button>
                                    </div>
                                </form>
                            )}
                            <div>
                                {error ? (
                                    <div>
                                        <h3 className="pt-5">
                                            Oops
                                        </h3>
                                        <p className="alert alert-danger">
                                            We could not reset your password with the details provided, please try
                                            again.
                                        </p>
                                    </div>
                                ) : (
                                    <div/>
                                )}

                            </div>
                        </div>
                    )}
                </AccountProvider>
            </div>
        );
    }
};

PasswordResetPage.propTypes = {};

module.exports = PasswordResetPage;
