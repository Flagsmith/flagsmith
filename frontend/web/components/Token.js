import React from 'react';
import { Component } from 'react';

class Token extends Component {
    constructor(props) {
        super();
        this.state = {
            showToken: !!props.show,
        };
    }

    render() {
        if (!this.props.token) return null;
        return (
            <Row>
                <Input
                  inputProps={{
                      readOnly: true,
                  }} value={this.state.showToken ? this.props.token : this.props.token.split('').map(v => '*').join('').trim()} style={this.props.style}
                  className={`${this.state.showToken ? 'font-weight-bold' : ''}`}
                />
                {this.props.show ? (
                    <ButtonOutline
                      style={{ width: 80 }} className="btn-secondary ml-2 mr-4" onClick={() => {
                          navigator.clipboard.writeText(this.props.token);
                          toast('Copied');
                      }}
                    >Copy
                    </ButtonOutline>

                ) : (
                    <Button style={{ width: 80 }} className="ml-2 mr-4" onClick={() => this.setState({ showToken: !this.state.showToken })}>{this.state.showToken ? 'Hide' : 'Show'}</Button>

                )}
            </Row>
        );
    }
}

export default Token;
