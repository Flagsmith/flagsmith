import React from 'react';

const AlertBar = class extends React.Component {
    state = {}

    componentDidMount() {
        document.body.classList.add('alert-shown');
    }

    componentWillUnmount() {
        document.body.classList.remove('alert-shown', 'hide');
    }

    hide = () => {
        document.body.classList.add('hide');
        this.setState({ hide: true });
    }

    render() {
        return (
            <Row className={`alert-bar ${this.props.className || ''}${this.state.hide ? 'animated slideOut' : ''}`}>
                <Flex className="alert-bar__text">{this.props.children}</Flex>
                {!this.props.preventClose && (
                    <a className="close-btn" onClick={this.hide}><span className="icon ion-md-close"/></a>
                )}
            </Row>
        );
    }
};

module.exports = AlertBar;
