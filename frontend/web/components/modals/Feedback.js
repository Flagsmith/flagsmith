import React, { Component } from 'react';

const Feedback = class extends Component {
    static displayName = 'Feedback'

    constructor(props, context) {
        super(props, context);
        this.state = {
            isSending: false,
        };
    }

    close() {
        closeModal();
    }

    componentDidMount = () => {
        this.focusTimeout = setTimeout(() => {
            this.nameInput.focus();
            this.focusTimeout = null;
        }, 500);
    };

    componentWillUnmount() {
        if (this.focusTimeout) {
            clearTimeout(this.focusTimeout);
        }
    }

    isValid = () => {
        if (!this.state.name || this.state.name.trim().length === 0) {
            return false;
        }

        if (!this.state.email || !Utils.isValidEmail(this.state.email)) {
            return false;
        }

        if (!this.state.comments || this.state.comments.trim().length === 0) {
            return false;
        }

        return true;
    }

    sendFeedback = () => {
        this.setState({ isSending: true });
        const { name, email, comments } = this.state;

        const url = 'https://post.formlyapp.com/bullet-train';
        const options = {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=utf-8',
            },
            body: JSON.stringify({
                name,
                email,
                comments,
            }),
        };

        if (E2E && document.getElementById('e2e-request')) {
            const payload = {
                url,
                options,
            };
            document.getElementById('e2e-request').innerText = JSON.stringify(payload);
        }

        fetch(url, options)
            .then((res) => {
                const isSuccess = res.status >= 200 && res.status < 300;
                this.close();
                toast(isSuccess ? 'Feedback sent' : 'Failed to send, try again later');
            });
    }

    render() {
        const { name, email, comments, isSending } = this.state;
        return (
            <div>
                <form onSubmit={(e) => {
                    e.preventDefault();
                    this.sendFeedback();
                }}
                >
                    <InputGroup
                      ref={e => this.nameInput = e}
                      inputProps={{
                          name: 'name',
                          className: 'full-width',
                      }}
                      onChange={e => this.setState({
                          name: Utils.safeParseEventValue(e),
                      })}
                      value={name}
                      isValid={name && name.trim().length}
                      type="text" title="Name"
                      placeholder=""
                    />
                    <InputGroup
                      ref={e => this.emailInput = e}
                      inputProps={{
                          name: 'email',
                          className: 'full-width',
                      }}
                      onChange={e => this.setState({
                          email: Utils.safeParseEventValue(e),
                      })}
                      value={email}
                      isValid={email && Utils.isValidEmail(email)}
                      type="text" title="Email"
                      placeholder=""
                    />
                    <FormGroup>
                        <div>
                            <strong>
                                Comments
                            </strong>
                        </div>
                        <textarea
                          name="comments" rows={5}
                          onChange={e => this.setState({ comments: Utils.safeParseEventValue(e) })}
                        />
                    </FormGroup>
                </form>
                <div className="text-right">
                    <Button
                      disabled={isSending || !this.isValid()} onClick={this.sendFeedback}
                    >
                        {isSending ? 'Sending' : 'Send'}
                    </Button>
                </div>
            </div>
        );
    }
};

Feedback.propTypes = {};

module.exports = Feedback;
