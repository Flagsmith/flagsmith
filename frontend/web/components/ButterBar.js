import React from 'react';
import { Component } from 'react';
import ConfigProvider from '../../common/providers/ConfigProvider';


class ButterBar extends Component {
    state = {};

    render() {
        return <>
            {Utils.getFlagsmithValue('butter_bar') && !Utils.getFlagsmithHasFeature('read_only_mode')&&(
                <div
                    dangerouslySetInnerHTML={{ __html: Utils.getFlagsmithValue('butter_bar') }}
                    className="butter-bar"
                />
            )}
            {Utils.getFlagsmithHasFeature('read_only_mode') && (
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
