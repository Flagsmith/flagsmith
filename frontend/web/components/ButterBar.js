import React from 'react';
import { Component } from 'react';
import ConfigProvider from 'common/providers/ConfigProvider';
import ProjectStore from 'common/stores/project-store'
class ButterBar extends Component {
    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor() {
        super();
        ES6Component(this)
    }

    render() {
        let environmentBanner;
        const matches = document.location.href.match(/\/environment\/([^/]*)/)
        const environment = matches && matches[1];
        if (environment) {
            const environmentDetail = ProjectStore.getEnvironment(environment)
            if(environmentDetail && environmentDetail.banner_text) {
                return (
                        <div
                            className="butter-bar"
                            style={{backgroundColor:environmentDetail.banner_colour, color:'white', fontWeight:'500'}}
                        >
                            {environmentDetail.banner_text}
                        </div>
                    )
            }
        }
        return <>
            {Utils.getFlagsmithValue('butter_bar') && !Utils.getFlagsmithHasFeature('read_only_mode') && (
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
        </>;
    }
}

export default ConfigProvider(ButterBar);
