import React, { Component } from 'react';
import { Link } from 'react-router';

export default class NotFoundView extends Component {
    static displayName = 'NotFoundPage'

    componentDidMount = () => {
        API.trackPage(Constants.pages.NOT_FOUND);
    };

    render() {
        return (
            <div className="container app-container text-center">
                <h1 className="pt-5">Oops, we can't seem to find this page!</h1>
                <hr/>
                <Link to="/">Back To Home View</Link>
            </div>
        );
    }
}
