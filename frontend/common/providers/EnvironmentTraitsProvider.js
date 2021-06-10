import React, { Component } from 'react';
import _data from '../data/base/_data';

const IdentityListProvider = class extends Component {
  static displayName = 'IdentityListProvider'

  constructor(props, context) {
      super(props, context);
      this.state = {
          isLoading: true,
      };
      ES6Component(this);
  }

  componentDidMount() {
      this.get(this.props);
  }

  get = (props) => {
      _data.get(`${Project.api}environments/${props.environmentId}/trait-keys/`)
          .then((res) => {
              this.setState({
                  isLoading: false,
                  isDeleting: false,
                  traits: res.keys,
              });
          })
          .catch((e) => {
              this.setState({ error, isLoading: false });
          });
  }

  deleteTrait =(trait) => {
      this.setState({ isDeleting: true });
      _data.post(`${Project.api}environments/${this.props.environmentId}/delete-traits/`, { key: trait })
          .then(() => {
              this.get(this.props);
          });
  }

  render() {
      return (
          this.props.children({ ...this.state, deleteTrait: this.deleteTrait })
      );
  }
};

IdentityListProvider.propTypes = {};

module.exports = IdentityListProvider;
