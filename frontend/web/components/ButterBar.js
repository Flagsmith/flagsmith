import React from 'react';
import { Component } from 'react';
import ConfigProvider from '../../common/providers/ConfigProvider';


class ButterBar extends Component {
    state = {};

    render() {
        return <>
            {this.props.getValue('butter_bar') && !this.props.hasFeature('read_only_mode')&&(
                <div
                    dangerouslySetInnerHTML={{ __html: this.props.getValue('butter_bar') }}
                    className="butter-bar"
                />
            )}
            {this.props.hasFeature('read_only_mode') && (
                <div
                    className="butter-bar"
                >
                    Your organisation is over its usage limit, please <Link to="/organisation-settings">upgrade your plan</Link>.
                </div>
            )}
        </>
    }
}

export default ConfigProvider(ButterBar);
