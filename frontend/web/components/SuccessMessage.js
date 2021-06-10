// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import TheInput from 'material-ui-chip-input';

export default class ErrorMessage extends PureComponent {
  static displayName = 'ErrorMessage';

  render() {
      return (
          <div className="alert alert-success">
              {this.props.message}
          </div>
      );
  }
}
