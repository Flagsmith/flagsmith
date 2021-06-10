import React, { Component } from 'react';

const ComingSoon = class extends Component {
    static displayName = 'ComingSoon'

    componentDidMount() {
        API.trackPage(Constants.pages.COMING_SOON);
    }

    render() {
        return (
            <div className="app-container container">
                <h3 className="pt-5">Oops!</h3>
                <p>
                  It looks like you do not have permission to view this {Utils.fromParam().entity || 'page'}. Please contact a member with administrator privileges.
                </p>
            </div>
        );
    }
};

ComingSoon.propTypes = {};

module.exports = ComingSoon;
