import React from 'react';
import { FormGroup } from '@material-ui/core';
import data from '../../common/data/base/_data';
import ErrorMessage from './ErrorMessage';

const SamlForm = class extends React.Component {
    static displayName = 'SamlForm'

    constructor() {
        super();
        this.state = {};
    }

    submit = (e) => {
        if (this.state.isLoading || !this.state.saml) {
            return
        }
        Utils.preventDefault(e);
        this.setState({ error: false, isLoading: true });

        data.post(`${Project.api}auth/saml/${this.state.saml}/request/`)
            .then((res) => {
                if (res.headers && res.headers.Location) {
                    document.location.href = res.headers.Location
                } else {
                    this.setState({error:true})
                }
            })
            .catch(() => {
                this.setState({ error: true, isLoading: false });
            });
    }

    render() {
        return (
            <form onSubmit={this.submit} className="saml-form" id="pricing">
                <InputGroup
                  inputProps={{ className: 'full-width' }}
                  onChange={e => this.setState({ saml: Utils.safeParseEventValue(e) })}
                  value={this.state.saml}
                  type="text" title="Organisation Name"
                />
                {
                    this.state.error && <ErrorMessage error="Please check your organisation name and try again."/>
                }
                <div className="text-right">
                    <Button disabled={this.state.isLoading} type="submit" disabled={!this.state.saml}>
                        Continue
                    </Button>
                </div>

            </form>
        );
    }
};

SamlForm.propTypes = {
    children: RequiredElement,
    toggleComponent: OptionalFunc,
    title: RequiredString,
    defaultValue: OptionalBool,
};

module.exports = ConfigProvider(SamlForm);
