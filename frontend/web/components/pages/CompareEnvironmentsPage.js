// import propTypes from 'prop-types';
import React, { Component } from 'react';
import TabItem from '../base/forms/TabItem';
import Tabs from '../base/forms/Tabs';
import CompareEnvironments from '../CompareEnvironments';
import CompareFeatures from '../CompareFeatures';


class TheComponent extends Component {
    static displayName = 'TheComponent';

    static propTypes = {};

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props) {
        super();
        this.state = {
            tab:0
        };
    }


    render() {
        return (
            <div className="app-container container">
                <Tabs      value={this.state.tab}
                           onChange={(tab) => {
                               this.setState({ tab });
                           }}>
                    <TabItem tabLabel={`Environments`}>
                        <div className="mt-2">
                            <CompareEnvironments projectId={this.props.match.params.projectId} environmentId={this.props.match.params.environmentId}/>
                        </div>
                    </TabItem>
                    <TabItem tabLabel={`Feature Values`}>
                        <div className="mt-2">
                            <CompareFeatures projectId={this.props.match.params.projectId}/>
                        </div>
                    </TabItem>
                </Tabs>
            </div>
        );
    }
}

module.exports = hot(module)(ConfigProvider(TheComponent));
