import React, { Component } from 'react'
import makeAsyncScriptLoader from 'react-async-script'
import _data from 'common/data/base/_data'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import InfoMessage from 'components/InfoMessage'
import Icon from 'components/Icon'
import firstpromoter from 'project/firstPromoter'

const PaymentButton = (props) => {
  const activeSubscription = AccountStore.getOrganisationPlan(
    AccountStore.getOrganisation().id,
  )

  if (activeSubscription) {
    return (
      <a
        onClick={() => {
          Chargebee.getInstance().openCheckout({
            hostedPage() {
              return _data.post(
                `${Project.api}organisations/${
                  AccountStore.getOrganisation().id
                }/get-hosted-page-url-for-subscription-upgrade/`,
                {
                  plan_id: props['data-cb-plan-id'],
                },
              )
            },
            success: (res) => {
              AppActions.updateSubscription(res)
              if (this.props.isDisableAccount) {
                window.location.href = `/organisations`
              }
            },
          })
        }}
        className={props.className}
        href='#'
      >
        {props.children}
      </a>
    )
  }
  return (
    <a
      href='javascript:void(0)'
      data-cb-type='checkout'
      data-cb-plan-id={props['data-cb-plan-id']}
      className={props.className}
    >
      {props.children}
    </a>
  )
}
const Payment = class extends Component {
  static displayName = 'Payment'

  constructor(props, context) {
    super(props, context)
    this.state = {}
  }

  componentDidMount = () => {
    API.trackPage(Constants.modals.PAYMENT)
  }

  onSave = () => {
    toast('Account Updated')
  }
  render() {
    const viewOnly = this.props.viewOnly
    const isAWS = AccountStore.getPaymentMethod() === 'AWS_MARKETPLACE'
    if (isAWS) {
      return (
        <div className='col-md-8'>
          <InfoMessage>
            Customers with AWS Marketplace subscriptions will need to{' '}
            <a
              href='https://www.flagsmith.com/contact-us'
              target='_blank'
              rel='noreferrer'
            >
              contact us
            </a>
          </InfoMessage>
        </div>
      )
    }
    return (
      <div>
        <AccountProvider onSave={this.onSave} onRemove={this.onRemove}>
          {({ organisation }) => {
            const plan =
              (organisation &&
                organisation.subscription &&
                organisation.subscription.plan) ||
              ''
            return (
              <div className='col-md-12'>
                <Row space className='mb-4'>
                  <h5>Manage Payment Plan</h5>
                  {this.props.isDisableAccountText && (
                    <Row>
                      <h7>
                        {this.props.isDisableAccountText}{' '}
                        <a
                          target='_blank'
                          href='mailto:support@flagsmith.com'
                          rel='noreferrer'
                        >
                          support@flagsmith.com
                        </a>
                      </h7>
                    </Row>
                  )}
                </Row>
                <Row className='pricing-container align-start'>
                  <Flex className='pricing-panel p-2'>
                    <div className='panel panel-default'>
                      <div className='panel-content p-3 pt-4'>
                        <Row className='pt-4 justify-content-center'>
                          <Icon name='flash' width={32} />
                          <h4 className='mb-0 ml-2'>Start-Up</h4>
                        </Row>
                        <Row className='pt-3 justify-content-center'>
                          <h5 className='mb-0 align-self-start'>$</h5>
                          <h1 className='mb-0'>
                            {this.state.yearly ? '40' : '45'}
                          </h1>
                        </Row>
                        <div className='pricing-type pt-1 pb-4'>
                          Billed Monthly
                        </div>
                        {!viewOnly ? (
                          this.state.yearly ? (
                            <PaymentButton
                              data-cb-plan-id='startup-annual-v2'
                              className='btn btn-primary full-width mt-3'
                              isDisableAccount={this.props.isDisableAccountText}
                            >
                              {plan.includes('startup') ? 'Purchased' : 'Buy'}
                            </PaymentButton>
                          ) : (
                            <PaymentButton
                              data-cb-plan-id='startup-v2'
                              className='btn btn-primary full-width mt-3'
                              isDisableAccount={this.props.isDisableAccountText}
                            >
                              {plan.includes('startup') ? 'Purchased' : 'Buy'}
                            </PaymentButton>
                          )
                        ) : null}
                      </div>
                      <div className='panel-footer mt-3'>
                        <ul className='pricing-features mb-0 px-2'>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Up to
                                <strong> 1,000,000</strong> requests per month
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                <strong>3</strong> Team Members
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Unlimited Projects</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Unlimited Feature Flags
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Unlimited Environments</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Unlimited Identities and Segments
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>3rd Party Integrations</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>A/B and MVT Testing</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Online Ts and Cs</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Email Technical Support
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Scheduled Flags</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Two-Factor Authentication (2FA)
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <Icon
                                name='minus-circle'
                                fill='rgba(101, 109, 123, 0.16)'
                              />
                              <div className='ml-2 disabled'>
                                User Roles and Permissions
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <Icon
                                name='minus-circle'
                                fill='rgba(101, 109, 123, 0.16)'
                              />
                              <div className='ml-2 disabled'>
                                Change Requests
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <Icon
                                name='minus-circle'
                                fill='rgba(101, 109, 123, 0.16)'
                              />
                              <div className='ml-2 disabled'>Audit Logs</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <Icon
                                name='minus-circle'
                                fill='rgba(101, 109, 123, 0.16)'
                              />
                              <div className='ml-2 disabled'>
                                SAML Authentication
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <Icon
                                name='minus-circle'
                                fill='rgba(101, 109, 123, 0.16)'
                              />
                              <div className='ml-2 disabled'>
                                On-Boarding & Training
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-2 pricing-features-item'>
                              <Icon
                                name='minus-circle'
                                fill='rgba(101, 109, 123, 0.16)'
                              />
                              <div className='ml-2 disabled'>
                                Optional On Premises Installation
                              </div>
                            </Row>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </Flex>
                  <Flex className='pricing-panel p-2'>
                    <div className='panel panel-default'>
                      <div
                        className='panel-content  p-3 pt-4'
                        style={{ backgroundColor: 'rgba(39, 171, 149, 0.08)' }}
                      >
                        <span className='featured'>Most Popular</span>
                        <Row className='pt-4 justify-content-center'>
                          <Icon name='layers' width={32} />
                          <h4 className='mb-0 ml-2'>Scale-Up</h4>
                        </Row>
                        <Row className='pt-3 justify-content-center'>
                          <h5 className='mb-0 align-self-start'>$</h5>
                          <h1 className='mb-0'>
                            {this.state.yearly ? '180' : '200'}
                          </h1>
                        </Row>
                        <div className='pricing-type pt-1 pb-4'>
                          Billed Monthly
                        </div>
                        {!viewOnly ? (
                          this.state.yearly ? (
                            <PaymentButton
                              data-cb-plan-id='scale-up-annual-v2'
                              className='btn btn-success full-width mt-3'
                              isDisableAccount={this.props.isDisableAccountText}
                            >
                              {plan.includes('scale-up') ? 'Purchased' : 'Buy'}
                            </PaymentButton>
                          ) : (
                            <PaymentButton
                              data-cb-plan-id='scale-up-v2'
                              className='btn btn-success full-width mt-3'
                              isDisableAccount={this.props.isDisableAccountText}
                            >
                              {plan.includes('scale-up') ? 'Purchased' : 'Buy'}
                            </PaymentButton>
                          )
                        ) : null}
                      </div>
                      <div className='panel-footer mt-3'>
                        <ul className='pricing-features mb-0 px-2'>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Up to
                                <strong> 5,000,000</strong> requests per month
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                <strong>5+</strong> Team Members
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Unlimited Projects</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Unlimited Feature Flags
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Unlimited Environments</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Unlimited Identities and Segments
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>3rd Party Integrations</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>A/B and MVT Testing</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Online Ts and Cs</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Email Technical Support
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Scheduled Flags</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Two-Factor Authentication (2FA)
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                User Roles and Permissions
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Change Requests</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Audit Logs</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <Icon
                                name='minus-circle'
                                fill='rgba(101, 109, 123, 0.16)'
                              />
                              <div className='ml-2 disabled'>
                                SAML Authentication
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <Icon
                                name='minus-circle'
                                fill='rgba(101, 109, 123, 0.16)'
                              />
                              <div className='ml-2 disabled'>
                                On-Boarding & Training
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-2 pricing-features-item'>
                              <Icon
                                name='minus-circle'
                                fill='rgba(101, 109, 123, 0.16)'
                              />
                              <div className='ml-2 disabled'>
                                Optional On Premises Installation
                              </div>
                            </Row>
                          </li>
                        </ul>
                        <a
                          onClick={() => {
                            Utils.openChat()
                          }}
                          className='pricing-cta blue mt-4'
                          style={{ width: '100%' }}
                        >
                          Request more API calls
                        </a>
                      </div>
                    </div>
                  </Flex>
                  <Flex className='pricing-panel p-2'>
                    <div className='panel panel-default'>
                      <div className='panel-content p-3 pt-4'>
                        <span className='featured'>
                          Optional On-Prem Install
                        </span>
                        <Row className='pt-4 justify-content-center'>
                          <Icon name='flash' width={32} />
                          <h4 className='mb-0 ml-2'>Enterprise</h4>
                        </Row>
                        <Row className='pt-3 justify-content-center'>
                          <h2 style={{ marginBottom: 6 }}>Contact Us</h2>
                        </Row>
                        <div className='pricing-type pt-1 pb-4'>
                          For Enterprise Pricing
                        </div>
                        {!viewOnly ? (
                          <Button
                            onClick={() => {
                              Utils.openChat()
                            }}
                            className='full-width mt-3'
                          >
                            Contact Us
                          </Button>
                        ) : null}
                      </div>
                      <div className='panel-footer mt-3'>
                        <ul className='pricing-features mb-0 px-2'>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                <strong> 5,000,000+</strong> requests per month
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                <strong>5+</strong> Team Members
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <Icon name='checkmark-circle' fill='#27AB95' />
                              <div className='ml-2'>Unlimited Projects</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Unlimited Feature Flags
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Unlimited Environments</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Unlimited Identities and Segments
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>3rd Party Integrations</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>A/B and MVT Testing</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Amendable MSA</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                Priority Real Time Technical Support with the
                                Engineering team over Slack or Discord
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Scheduled Flags</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                2FA, SAML, Okta, ADFS and LDAP Authentication
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>
                                User Roles and Permissions
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <Icon name='checkmark-circle' fill='#27AB95' />
                              <div className='ml-2'>Change Requests</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Audit Logs</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>On-Boarding & Training</div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-2 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#27AB95' />
                              </span>
                              <div className='ml-2'>Uptime and Support SLA</div>
                            </Row>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </Flex>
                </Row>
              </div>
            )
          }}
        </AccountProvider>
      </div>
    )
  }
}

const WrappedPayment = makeAsyncScriptLoader(
  'https://js.chargebee.com/v2/chargebee.js',
  {
    removeOnUnmount: true,
  },
)(ConfigProvider(Payment))

Payment.propTypes = {}

module.exports = (props) => (
  <WrappedPayment
    {...props}
    asyncScriptOnLoad={() => {
      Chargebee.init({
        site: Project.chargebee.site,
      })
      Chargebee.registerAgain()
      firstpromoter()
      Chargebee.getInstance().setCheckoutCallbacks(() => ({
        success: (hostedPageId) => {
          AppActions.updateSubscription(hostedPageId)
        },
      }))
    }}
  />
)
