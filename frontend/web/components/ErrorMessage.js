// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import TheInput from 'material-ui-chip-input';

export default class ErrorMessage extends PureComponent {
  static displayName = 'ErrorMessage';

  render() {
      return this.props.error? (
          <div className="alert alert-danger">
              {this.props.error}
          </div>
      ) : null;
  }
}
