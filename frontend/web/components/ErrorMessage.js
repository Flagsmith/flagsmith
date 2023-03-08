// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import TheInput from 'material-ui-chip-input';

export default class ErrorMessage extends PureComponent {
  static displayName = 'ErrorMessage';

  render() {
      return this.props.error ? (
          <div className="alert alert-danger">
              {typeof this.props.error === "object"? Object.keys(this.props.error).map((v)=>`${v}: ${this.props.error[v]}`).join("\n"): this.props.error}
          </div>
      ) : null;
  }
}
