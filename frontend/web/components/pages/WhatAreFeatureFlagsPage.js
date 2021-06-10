import React, { Component } from 'react';

const WhatAreFeatureFlagsPage = class extends Component {
    static displayName = 'WhatAreFeatureFlagsPage'

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    componentDidMount() {
        API.trackPage(Constants.pages.WHAT_ARE_FEATURE_FLAGS);
    }

    render() {
        return (
            <div className="app-container">
                <FormGroup className="striped-section">
                    <div className="container">
                        <h3>What are feature flags?</h3>
                        <div className="row">
                            <div className="col-xl-6">
                                <p>
                                    A Feature Flag is a technique to turn some functionality of your application off,
                                    via configuration, without deploying new code. If you’re employing CI/CD and
                                    releasing
                                    often they’re pretty important.
                                </p>
                                <p>
                                    With Flagsmith, feature flags can be turned on and off per environment, also you
                                    can enable flags for specific users. For example, this could be used to show
                                    features to your internal team in production or for beta testers.
                                </p>
                            </div>
                            <div className="col-xl-6">
                                <p className="faint text-center">
                                    EXAMPLE: our interactive try it panels throughout the site are controlled by feature
                                    flags.
                                </p>
                                <div className="text-center">
                                    <Gif
                                      width="100%" pausedSrc="/images/feature-flag.png"
                                      src="/images/feature-flag.gif"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </FormGroup>
                <FormGroup className="striped-section">
                    <div className="container">
                        <h3>What is remote config?</h3>
                        <div className="row">
                            <div className="col-xl-6">
                                <p>
                                    It's great being able to turn features on and off without doing a build, but with
                                    some
                                    features,
                                    it's not as simple as that. This is where remote config comes in.
                                    Often there's a need to configure feature properties, for example updating some text
                                    to
                                    promote an
                                    in-app currency sale or even the copy on our homepage.
                                </p>
                                <p>
                                    Similarly with feature flags, Flagsmith lets you configure these per environment
                                    and for specific users. With our upcoming user segments feature, this could be used
                                    to show different messaging or environment variables to power user groups,
                                    mobile/browser specific users and
                                    much more.
                                </p>
                            </div>
                            <div className="col-xl-6">
                                <p className="faint text-center">
                                    EXAMPLE: our homepage sections are controlled with remote config
                                </p>
                                <div className="text-center">
                                    <Gif
                                      width="100%" pausedSrc="/images/remote-config.png"
                                      src="/images/remote-config.gif"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </FormGroup>
                <FormGroup className="striped-section">
                    <div className="container">
                        <h3>What benefits does this bring?</h3>

                        <p>
                            People who are not used to continuous integration might be wondering: why didn't I just
                            release the feature the way I normally would? Some of the reasons for feature flags being
                            such a good approach:
                        </p>
                        <ul>
                            <li>
                                It introduces the ability to test code in production with gradual/targeted rollouts to
                                specific
                                users.
                            </li>
                            <li>
                                It empowers non-technical team members to manage feature releases.
                            </li>
                            <li>
                                It enables testing of features early, against an up-to-date codebase. CI means we're
                                constantly
                                testing features on a very close representation to what is running in production.
                            </li>
                            <li>
                                It allows you to introduce beta programs to get early user feedback.
                            </li>
                            <li>
                                It reduces the need to rollback code with the ability to turn off features remotely in
                                the
                                event
                                of an emergency.
                            </li>
                        </ul>
                    </div>
                </FormGroup>
            </div>
        );
    }
};

WhatAreFeatureFlagsPage.propTypes = {};

module.exports = WhatAreFeatureFlagsPage;
