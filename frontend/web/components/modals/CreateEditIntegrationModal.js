import React, { Component } from 'react';
import EnvironmentSelect from '../EnvironmentSelect';
import _data from '../../../common/data/base/_data';
import ErrorMessage from '../ErrorMessage';

const CreateEditIntegration = class extends Component {
    static displayName = 'CreateEditIntegration'

    constructor(props, context) {
        super(props, context);
        this.state = { data: this.props.data ? { ...this.props.data } : {} };
    }


    update = (key, e) => {
        this.setState({ data: {
            ...this.state.data,
            [key]: Utils.safeParseEventValue(e),
        },
        });
    }

    onComplete = () => {
        closeModal();
        this.props.onComplete && this.props.onComplete();
    }

    submit = (e) => {
        Utils.preventDefault(e);
        if (this.state.isLoading) {
            return;
        }
        this.setState({ isLoading: true });
        if (this.props.integration.perEnvironment) {
            if (this.props.integration.isOauth) {
                return _data.get(`${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}/oauth/`, {
                    redirect_url: document.location.href,
                }).then((res) => {

                });
            }
            if (this.props.data) {
                _data.put(`${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}/${this.props.data.id}/`, this.state.data)
                    .then(this.onComplete).catch(this.onError);
            } else {
                _data.post(`${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}/`, this.state.data)
                    .then(this.onComplete).catch(this.onError);
            }
        } else if (this.props.integration.isOauth){
            return _data.get(`${Project.api}projects/${this.props.projectId}/integrations/${this.props.id}/oauth/`, {
                redirect_url: document.location.href,
            }).then((res) => {

            });
        } else if (this.props.data) {
            _data.put(`${Project.api}projects/${this.props.projectId}/integrations/${this.props.id}/${this.props.data.id}/`, this.state.data)
                .then(this.onComplete).catch(this.onError);
        } else {
            _data.post(`${Project.api}projects/${this.props.projectId}/integrations/${this.props.id}/`, this.state.data)
                .then(this.onComplete).catch(this.onError);
        }
    }

    onError = (res) => {
        const defaultError = 'There was an error adding your integration, please the details and try again.';
        res.text().then((error) => {
            let err = error;
            try {
                err = JSON.parse(error);
                this.setState({
                    error: err[0] || defaultError,
                    isLoading: false,
                });
            } catch (e) {}
        }).catch((e) => {
            this.setState({
                error: defaultError,
                isLoading: false,
            });
        });
    }

    render() {
        return (
            <form
              data-test="create-project-modal"
              id="create-project-modal" onSubmit={this.submit}
            >
                {this.props.integration.perEnvironment && (
                <div className="mb-2">
                    <label>Flagsmith Environment</label>
                    <EnvironmentSelect readOnly={!!this.props.data || this.props.readOnly} value={this.state.data.flagsmithEnvironment} onChange={environment => this.update('flagsmithEnvironment', environment)}/>
                </div>
                )}
                {this.props.integration.fields && this.props.integration.fields.map(field => (
                  <>
                      <div>
                          <label htmlFor={field.label.replace(/ /g, '')}>
                              {this.props.readOnly ? (
                                  <ButtonLink>
                                      {field.label}
                                  </ButtonLink>
                              ) : field.label}
                          </label>
                      </div>
                      {this.props.readOnly ? (
                          <div className="mb-2">
                              {this.state.data[field.key]}
                          </div>
                      ) : (
                          <Input
                            id={field.label.replace(/ /g, '')}
                            ref={e => this.input = e}
                            value={this.state.data[field.key]}
                            onChange={e => this.update(field.key, e)}
                            isValid={!!this.state.data[field.key]}
                            type="text"
                            className="full-width mb-2"
                          />
                      )}

                  </>
                ))}
                <ErrorMessage error={this.state.error}/>
                {!this.props.readOnly && (
                    <div className="text-right">
                        <Button disabled={this.state.isLoading} type="submit">
                            {this.props.integration.isOauth ? 'Authorise' : 'Save'}
                        </Button>
                    </div>
                )}

            </form>
        );
    }
};

CreateEditIntegration.propTypes = {};

module.exports = CreateEditIntegration;
