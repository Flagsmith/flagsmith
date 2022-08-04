// import propTypes from 'prop-types';
import React, { Component } from 'react';
import data from '../../common/data/base/_data';
import ErrorMessage from './ErrorMessage';
import SuccessMessage from './SuccessMessage';
import PlayIcon from './svg/PlayIcon';

export default class TheComponent extends Component {
  static displayName = 'TestWebhook';

  static propTypes = {};

  constructor(props) {
      super(props);
      this.state = {};
  }

  submit = () => {
      this.setState({ loading: true, error: false, success: false });
      data.post(this.props.webhook, JSON.parse(this.props.json))
          .then(() => {
              this.setState({ success: true, loading: false });
          })
          .catch((e) => {
              if (e.text) {
                  e.text().then(error => this.setState({ error: `The server returned an error: ${error}` }));
              } else {
                  this.setState({ error: 'There was an error posting to your webhook.', loading: false });
              }
          });
  }

  render() {
      const {
          submit,
          state: {
              loading,
              error,
              success,
          } } = this;
      return (
          <div>
              {error && <ErrorMessage error={this.state.error}/>}
              {success && <SuccessMessage message="Your API returned with a successful 200 response."/>}
              <Button
                id="try-it-btn" disabled={loading||!this.props.webhook} onClick={submit}
                className="btn btn--with-icon primary"
              >
                  Test your webhook
                  {' '}
                  <PlayIcon className="btn__icon btn__icon--small" alt="Run"/>
              </Button>
          </div>
      );
  }
}
