import React from 'react';
import { ContactForm } from './ContactForm';

const PricingPanel = class extends React.Component {
    static displayName = 'PricingPanel'

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }


    render() {
        const { hasFeature, redirect } = this.props;

        return (
            <div className="pricing" id="pricing">
                <div className="container">
                    <h2 className="text-center margin-bottom margin-top">Start using Bullet Train for free</h2>
                    <p className="text-center">Then increase your plan as your business grows.</p>
                    <div className="col-md-12">
                        <div className="flex-row row-center">
                            <div className="col-md-3 pricing-panel">
                                <div className="panel panel-default">
                                    <div className="panel-content">
                                        <p className="featured" />
                                        <p className="pricing-price">Free</p>
                                        <img src="/static/images/growth.svg" alt="free icon" className="pricing-icon"/>
                                        <p className="pricing-type">Free</p>
                                        <p className="text-small text-center">more flags than the UN</p>
                                        <Link to={`/${redirect}#sign-up`} className="pricing-cta blue" onClick={Utils.scrollToSignUp}>Sign up</Link>
                                    </div>
                                    <div className="panel-footer">
                                        <p className="text-small text-center link-style">What's included</p>
                                        <ul className="pricing-features">
                                            <li><p>Up to <strong>20,000</strong> requests per month</p></li>
                                            <li>
                                                <p>
                                                    <strong>1</strong> Team Member
                                                </p>
                                            </li>
                                            <li><p>Unlimited Environments</p></li>
                                            <li><p>Unlimited Feature Flags</p></li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div className="col-md-3 pricing-panel">
                                <div className="panel panel-default">
                                    <div className="panel-content">
                                        <p className="featured" />
                                        <p className="pricing-price">Start-Up</p>
                                        <img src="/static/images/startup.svg" alt="Startup icon" className="pricing-icon"/>
                                        <p className="pricing-type">$29</p>
                                        <p className="text-small text-center">billed monthly</p>
                                        <Link to={`/${redirect}#sign-up`} className="pricing-cta blue" onClick={Utils.scrollToSignUp}>Sign up</Link>
                                    </div>
                                    <div className="panel-footer">
                                        <p className="text-small text-center link-style">What's included</p>
                                        <ul className="pricing-features">
                                            <li>
                                                <p>Up to <strong>250,000</strong>
                                                    {' '}
                                                    {' '}
requests per month
                                                </p>
                                            </li>
                                            <li>
                                                <p>Up to <strong>3</strong>
                                                    {' '}
Team Members
                                                </p>
                                            </li>
                                            <li><p>Unlimited Environments</p></li>
                                            <li><p>Unlimited Feature Flags</p></li>
                                            <li><p>Email Technical Support</p></li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div className="col-md-3 pricing-panel">
                                <div className="panel panel-default">
                                    <div className="panel-content">
                                        <p className="featured">Most Popular</p>
                                        <p className="pricing-price">Scale-Up</p>
                                        <img src="/static/images/pricing-scale-up.svg" alt="Scale-up icon" className="pricing-icon"/>
                                        <p className="pricing-type">$99</p>
                                        <p className="text-small text-center">billed monthly</p>
                                        <Link to={`/${redirect}#sign-up`} className="pricing-cta blue" onClick={Utils.scrollToSignUp}>Sign up</Link>
                                    </div>
                                    <div className="panel-footer">
                                        <p className="text-small text-center link-style">What's included</p>
                                        <ul className="pricing-features">
                                            <li>
                                                <p>Up to <strong>2 million</strong>
                                                    {' '}
                                                    {' '}
requests per month
                                                </p>
                                            </li>
                                            <li>
                                                <p>Up to <strong>10</strong>
                                                    {' '}
Team Members
                                                </p>
                                            </li>
                                            <li><p>All Startup Features</p></li>
                                            <li><p>Audit logs</p></li>
                                            <li><p>Private Discord Technical Support</p></li>
                                        </ul>

                                    </div>
                                </div>
                            </div>
                            <div className="col-md-3 pricing-panel">
                                <div className="panel panel-default">
                                    <div className="panel-content">
                                        <p className="featured" />
                                        <p className="pricing-price">Enterprise</p>
                                        <img src="/static/images/cubes.svg" alt="Enterprise icon" className="pricing-icon"/>
                                        <p className="pricing-type">Contact Us</p>
                                        <p className="text-small text-center">for enterprise pricing</p>
                                        <a
                                          onClick={() => {
                                              openModal('Contact Sales', <ContactForm onComplete={closeModal}/>);
                                          }} className="pricing-cta blue"
                                        >Contact Us
                                        </a>
                                    </div>

                                    <div className="panel-footer">
                                        <p className="text-small text-center link-style">What's included</p>
                                        <ul className="pricing-features">
                                            <li>
                                                <p>Over <strong>2 million</strong>
                                                    {' '}
                                                    {' '}
requests per month
                                                </p>
                                            </li>
                                            <li>
                                                <p>Over <strong>10</strong>
                                                    {' '}
Team Members
                                                </p>
                                            </li>
                                            <li><p>All Startup Features</p></li>
                                            <li><p>SAML, 2-factor and SSO options</p></li>
                                            <li><p>Telephone and Discord Technical Support</p></li>
                                            <li><p>Optional On Premise Installation</p></li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
};

PricingPanel.propTypes = {
    children: RequiredElement,
    toggleComponent: OptionalFunc,
    title: RequiredString,
    defaultValue: OptionalBool,
};

module.exports = ConfigProvider(PricingPanel);
