import React from 'react';

const Blocked = class extends React.Component {
    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    static displayName = 'HomePage';

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }


    render = () => (
        <div className="fullscreen-container maintenance fullscreen-container__grey justify-content-center">
            <div className="col-md-6 mt-5" id="sign-up">
                <h1>Please get in touch</h1>
                Your organisation has been disabled, if you think this has been done in error please contact
                {
                      <>
                          {' '} <a target="_blank" href="mailto:support@bullet-train.io">support@bullet-train.io</a>.
                      </>
                }

            </div>
        </div>
    )
};

module.exports = ConfigProvider(Blocked);
