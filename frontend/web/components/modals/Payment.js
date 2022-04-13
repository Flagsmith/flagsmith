import React, { Component } from 'react';
import makeAsyncScriptLoader from 'react-async-script';
import { ContactForm } from '../ContactForm';
import _data from '../../../common/data/base/_data';

const PaymentButton = (props) => {
    const activeSubscription = AccountStore.getOrganisationPlan(AccountStore.getOrganisation().id);
    if (flagsmith.hasFeature('upgrade_subscription') && activeSubscription) {
        return (
            <a
              onClick={() => {
                  Chargebee.getInstance().openCheckout({
                      hostedPage() {
                          return _data.post(`${Project.api}organisations/${AccountStore.getOrganisation().id}/get-hosted-page-url-for-subscription-upgrade/`, {
                              plan_id: props['data-cb-plan-id'],
                          });
                      },
                      success: (res) => {
                          AppActions.updateSubscription(res);
                      },
                  });
              }}
              href="#"
              className={props.className}
            >
                {props.children}
            </a>
        );
    }
    return (
        <a
          href="javascript:void(0)"
          data-cb-type="checkout"
          data-cb-plan-id={props['data-cb-plan-id']}
          className={props.className}
        >
            {props.children}
        </a>
    );
};
const PaymentModal = class extends Component {
    static displayName = 'Payment'

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    componentDidMount = () => {
        API.trackPage(Constants.modals.PAYMENT);
    };

    onSave = () => {
        toast('Account Updated');
        closeModal();
    };

    componentWillReceiveProps(newProps) {
    }

    render() {
        const viewOnly = this.props.viewOnly;
        const { hasFeature, getValue } = this.props;


        return (
            <div className="app-container container">
                <AccountProvider onSave={this.onSave} onRemove={this.onRemove}>
                    {({
                        isLoading,
                        isSaving,
                        user,
                        organisation,
                    }, { createOrganisation, selectOrganisation, editOrganisation, deleteOrganisation }) => {
                        const plan = (organisation && organisation.subscription && organisation.subscription.plan) || '';
                        return (
                            <div>
                                <div>
                                    <div className="col-md-12">
                                        {flagsmith.hasFeature("annual_plans")&&(
                                            <div className="text-center mb-4">
                                                <Row className="justify-content-center">
                                                    <span className="mr-2">
                                                        Monthly
                                                    </span>
                                                    <Switch onMarkup={" "
                                                    } offMarkup={" "} checked={this.state.yearly} onChange={(yearly)=>this.setState({yearly})}/>
                                                    <span className="ml-2">
                                                        Yearly
                                                    </span>
                                                </Row>
                                            </div>
                                        )}
                                        <div className="flex-row align-start">
                                            <div className="col-md-4 pricing-panel">
                                                <div className="panel panel-default">
                                                    <div className="panel-content">
                                                        <p className="featured"/>
                                                        <p className="pricing-price">Start-Up</p>

                                                        <img
                                                          src="/static/images/startup.svg" alt="Startup icon"
                                                          className="pricing-icon"
                                                        />
                                                        <p className="pricing-type">{this.state.yearly?"$40":"$45"}</p>
                                                        <p className="text-small text-center">billed monthly</p>
                                                        {!viewOnly ? this.state.yearly? (
                                                            <PaymentButton
                                                              data-cb-plan-id={"startup-annual-v2"}
                                                              className="pricing-cta blue"
                                                            >
                                                                {plan.includes('startup') ? 'Purchased' : 'Buy'}
                                                            </PaymentButton>
                                                        ) : (
                                                            <PaymentButton
                                                                data-cb-plan-id={"startup-v2"}
                                                                className="pricing-cta blue"
                                                            >
                                                                {plan.includes('startup') ? 'Purchased' : 'Buy'}
                                                            </PaymentButton>
                                                        ) : null}
                                                    </div>
                                                    <div className="panel-footer">
                                                        <p className="text-small text-center link-style">What's included</p>
                                                        <ul className="pricing-features">
                                                            <li>
                                                                <p>
                                                                    {'Up to '}
                                                                    <strong>1,000,000</strong>
                                                                    {' '}
                                                                    requests per month
                                                                </p>
                                                            </li>
                                                            <li>
                                                                <p>
                                                                    <strong>3</strong>
                                                                    {' '}
                                                                    Team Members
                                                                </p>
                                                            </li>
                                                            <li><p>Unlimited Environments</p></li>
                                                            <li><p>Unlimited Feature Flags</p></li>
                                                            <li><p>Unlimited Identities and Segments</p></li>
                                                            <li><p>3rd Party Integrations</p></li>
                                                            <li><p>A/B and MVT Testing</p></li>
                                                            <li><p>Email Technical Support</p></li>
                                                            <li><p>Online Ts and Cs</p></li>
                                                        </ul>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="col-md-4 pricing-panel">
                                                <div className="panel panel-default">
                                                    <div className="panel-content">
                                                        <p className="featured">Most Popular</p>
                                                        <p className="pricing-price">Scale-Up</p>
                                                        <img
                                                          src="/static/images/pricing-scale-up.svg" alt="Scale-up icon"
                                                          className="pricing-icon"
                                                        />
                                                        <p className="pricing-type">{this.state.yearly?"$180":"$200"}</p>
                                                        <p className="text-small text-center">billed monthly</p>
                                                        {!viewOnly ? this.state.yearly? (
                                                            <PaymentButton
                                                                data-cb-plan-id={"scale-up-annual-v2"}
                                                              className="pricing-cta"
                                                            >
                                                                {plan.includes('scale-up') ? 'Purchased' : 'Buy'}
                                                            </PaymentButton>
                                                        ) : (
                                                            <PaymentButton
                                                                data-cb-plan-id={"scale-up-v2"}
                                                                className="pricing-cta"
                                                            >
                                                                {plan.includes('scale-up') ? 'Purchased' : 'Buy'}
                                                            </PaymentButton>
                                                        ) : null}
                                                    </div>
                                                    <div className="panel-footer">
                                                        <p className="text-small text-center link-style">What's included</p>
                                                        <ul className="pricing-features">
                                                            <li>
                                                                <p>
                                                                    Up to {' '}
                                                                    <strong>5,000,000</strong>
                                                                    {' '}
                                                                    requests per month
                                                                </p>
                                                            </li>
                                                            <li><p><strong>5</strong>{' '}Team Members</p></li>
                                                            <li><p>Unlimited Environments</p></li>
                                                            <li><p>Unlimited Feature Flags</p></li>
                                                            <li><p>Unlimited Identities and Segments</p></li>
                                                            <li><p>3rd Party Integrations</p></li>
                                                            <li><p>A/B and MVT Testing</p></li>
                                                            <li><p>Priority Email Technical Support</p></li>
                                                            <li><p>User Roles and Permissions</p></li>
                                                            <li><p>Audit Logs</p></li>
                                                            <li><p>2FA and SAML Authentication</p></li>
                                                            <li><p>Online Ts and Cs</p></li>
                                                        </ul>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="col-md-4 pricing-panel">
                                                <div className="panel panel-default">
                                                    <div className="panel-content">
                                                        <p className="featured">Optional On-Prem Install</p>
                                                        <p className="pricing-price">Enterprise</p>
                                                        <img
                                                          src="/static/images/cubes.svg" alt="Enterprise icon"
                                                          className="pricing-icon"
                                                        />
                                                        <p className="pricing-type">Contact Us</p>
                                                        <p className="text-small text-center">for enterprise pricing</p>
                                                        {!viewOnly ? (
                                                            <a
                                                              onClick={() => {
                                                                  openModal('Contact Sales', <ContactForm onComplete={closeModal}/>);
                                                              }}
                                                              href="#"
                                                              className="pricing-cta blue"
                                                            >
                                                                Contact Us
                                                            </a>
                                                        ) : null}
                                                    </div>

                                                    <div className="panel-footer">
                                                        <p className="text-small text-center link-style">What's included</p>
                                                        <ul className="pricing-features">
                                                            <li>
                                                                <p>
                                                                    <strong>5,000,000 +</strong> requests per month
                                                                </p>
                                                            </li>
                                                            <li>
                                                                <p>
                                                                    Over <strong>5</strong> Team Members
                                                                </p>
                                                            </li>
                                                            <li><p>Unlimited Environments</p></li>
                                                            <li><p>Unlimited Feature Flags</p></li>
                                                            <li><p>Unlimited Identities and Segments</p></li>
                                                            <li><p>3rd Party Integrations</p></li>
                                                            <li><p>A/B and MVT Testing</p></li>
                                                            <li><p>Priority Email Technical Support</p></li>
                                                            <li><p>User Roles and Permissions</p></li>
                                                            <li><p>2FA and SAML Authentication</p></li>
                                                            <li><p>Audit Logs</p></li>
                                                            <li><p>Uptime and Support SLA</p></li>
                                                            <li><p>On-Boarding &amp; Training</p></li>
                                                            <li><p>Amendable MSA</p></li>
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
                    }
                </AccountProvider>
            </div>
        );
    }
};

const WrappedPaymentModal = makeAsyncScriptLoader(ConfigProvider(PaymentModal), 'https://js.chargebee.com/v2/chargebee.js', {
    removeOnUnmount: true,
});

PaymentModal.propTypes = {};

module.exports = props => (
    <WrappedPaymentModal
      {...props} asyncScriptOnLoad={() => {
          Chargebee.init({
              site: Project.chargebee.site,
          });
          Chargebee.registerAgain();
          Chargebee.getInstance().setCheckoutCallbacks(cart => ({
              success: (hostedPageId) => {
                  AppActions.updateSubscription(hostedPageId);
              },
          }));
      }}
    />
);
