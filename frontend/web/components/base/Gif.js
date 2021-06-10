import React, { Component } from 'react';

const Gif = class extends Component {
    static displayName = 'Gif'

    constructor(props, context) {
        super(props, context);
        this.state = {
            paused: true,
        };
    }

    render() {
        return (
            <Flex
              onClick={() => this.setState({ paused: !this.state.paused })}
              className={`centered-container gif ${this.state.paused ? 'paused' : 'playing'}`}
            >
                <img
                  {...this.props}
                  alt="Pause"
                  src={this.state.paused ? this.props.pausedSrc : this.props.src}
                />
                <span className="ion ion-ios-play"/>
            </Flex>
        );
    }
};

Gif.propTypes = {};

module.exports = Gif;
