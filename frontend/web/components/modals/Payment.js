import React, { Component } from 'react'
import makeAsyncScriptLoader from 'react-async-script'
import _data from 'common/data/base/_data'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import InfoMessage from 'components/InfoMessage'
import Icon from 'components/Icon'
import firstpromoter from 'project/firstPromoter'
import Utils from 'common/utils/utils'
import AccountProvider from 'common/providers/AccountProvider'
import classNames from 'classnames'
import Switch from 'components/Switch'
import BlockedOrgInfo from 'components/BlockedOrgInfo'

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
    this.state = {
      yearly: true,
    }
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
                  {this.props.isDisableAccountText && (
                    <div className='d-lg-flex flex-lg-row align-items-end justify-content-between w-100 gap-4'>
                      <div>
                        <h4>
                          {this.props.isDisableAccountText}{' '}
                          <a
                            target='_blank'
                            href='mailto:support@flagsmith.com'
                            rel='noreferrer'
                          >
                            support@flagsmith.com
                          </a>
                        </h4>
                      </div>
                      <div>
                        <BlockedOrgInfo />
                      </div>
                    </div>
                  )}
                </Row>
                <div className='d-flex mb-4 font-weight-medium justify-content-center align-items-center gap-2'>
                  <h5
                    className={classNames('mb-0', {
                      'text-muted': !this.state.yearly,
                    })}
                  >
                    Pay Yearly (Save 10%)
                  </h5>
                  <Switch
                    checked={!this.state.yearly}
                    onChange={() => {
                      this.setState({ yearly: !this.state.yearly })
                    }}
                  />
                  <h5
                    className={classNames('mb-0', {
                      'text-muted': this.state.yearly,
                    })}
                  >
                    Pay Monthly
                  </h5>
                </div>
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
                          <h1 className='mb-0 d-flex align-items-end'>
                            {this.state.yearly ? '40' : '45'} <h5 className="fs-lg mb-0">/mo</h5>
                          </h1>
                        </Row>
                        {!viewOnly ? (
                          <>
                            <PaymentButton
                              data-cb-plan-id={Project.plans.startup.annual}
                              className={classNames(
                                'btn btn-primary btn-lg full-width mt-3',
                                { 'd-none': !this.state.yearly },
                              )}
                              isDisableAccount={this.props.isDisableAccountText}
                            >
                              {plan.includes('startup') ? 'Purchased' : '14 Day Free Trial'}
                            </PaymentButton>
                            <PaymentButton
                              data-cb-plan-id={Project.plans.startup.monthly}
                              className={classNames(
                                'btn btn-primary btn-lg full-width mt-3',
                                { 'd-none': this.state.yearly },
                              )}
                              isDisableAccount={this.props.isDisableAccountText}
                            >
                              {plan.includes('startup') ? 'Purchased' : '14 Day Free Trial'}
                            </PaymentButton>
                          </>
                        ) : null}
                      </div>
                      <div className="panel-footer mt-3">

                        <h5 className="m-2 mb-4">
                          All from <span className="text-primary">Free,</span> plus
                        </h5>
                        <ul className="pricing-features mb-0 px-2">
                          <li>
                            <Row className="mb-3 pricing-features-item">
                              <span>
                                <Icon name="checkmark-circle" fill="#27AB95" />
                              </span>
                              <div className="ml-2">
                                Up to
                                <strong> 1,000,000</strong> Requests per month
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className="mb-3 pricing-features-item">
                              <span>
                                <Icon name="checkmark-circle" fill="#27AB95" />
                              </span>
                              <div className="ml-2">
                                <strong>3</strong> Team members
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className="mb-3 pricing-features-item">
                              <span>
                                <Icon name="checkmark-circle" fill="#27AB95" />
                              </span>
                              <div className="ml-2">Unlimited projects</div>
                            </Row>
                          </li>

                          <li>
                            <Row className="mb-3 pricing-features-item">
                              <span>
                                <Icon name="checkmark-circle" fill="#27AB95" />
                              </span>
                              <div className="ml-2">Email technical support</div>
                            </Row>
                          </li>

                          <li>
                            <Row className="mb-3 pricing-features-item">
                              <span>
                                <Icon name="checkmark-circle" fill="#27AB95" />
                              </span>
                              <div className="ml-2">Scheduled flags</div>
                            </Row>
                          </li>
                          <li>
                            <Row className="mb-3 pricing-features-item">
                              <span>
                                <Icon name="checkmark-circle" fill="#27AB95" />
                              </span>
                              <div className="ml-2">Two-factor authentication (2FA)</div>
                            </Row>
                          </li>

                        </ul>
                      </div>
                    </div>
                  </Flex>
                  <Flex className='pricing-panel bg-primary900 text-white p-2'>
                    <div className='panel panel-default'>
                      <div className='panel-content p-3 pt-4'>
                        <span className='featured text-body'>
                          Optional <a className="text-primary fw-bold" target="_blank" href="https://www.flagsmith.com/on-premises-and-private-cloud-hosting">On Premise</a> or <a className="text-primary fw-bold" target="_blank" href="https://www.flagsmith.com/on-premises-and-private-cloud-hosting">Private Cloud</a> Install
                        </span>
                        <Row className='pt-4 justify-content-center'>
                          <Icon fill="white" name='flash' width={32} />
                          <h4 className='mb-0 ml-2 text-white'>Enterprise</h4>
                        </Row>
                        <Row className='pt-3 justify-content-center'>
                        </Row>
                        <div className='pricing-type text-secondary pt-1 pb-4'>
                          Maximum security and control
                        </div>
                        {!viewOnly ? (
                          <Button
                            onClick={() => {
                              Utils.openChat()
                            }}
                            className='full-width btn-lg btn-tertiary mt-3'
                          >
                            Contact Sales
                          </Button>
                        ) : null}
                      </div>
                      <div className='panel-footer mt-3'>
                        <h5 className="text-white m-2 mb-4">
                          All from <span className="text-secondary">Start-Up,</span> plus
                        </h5>
                        <ul className='pricing-features mb-0 px-2'>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#F7D56E' />
                              </span>
                              <div className='ml-2'>
                                <strong> 5,000,000+</strong> requests per month
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#F7D56E' />
                              </span>
                              <div className='ml-2'>
                                <strong>20+</strong> Team members
                              </div>
                            </Row>
                          </li>

                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#F7D56E' />
                              </span>
                              <div className='ml-2'>
                                Advanced hosting options
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#F7D56E' />
                              </span>
                              <div className='ml-2'>
                                Priority real time technical support with the engineering team over Slack or Discord
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#F7D56E' />
                              </span>
                              <div className='ml-2'>
                                Governance features – roles, permissions, change requests, audit logs
                              </div>
                            </Row>
                          </li>

                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#F7D56E' />
                              </span>
                              <div className='ml-2'>
                                Features for maximum security
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#F7D56E' />
                              </span>
                              <div className='ml-2'>
                                Optional on premises installation
                              </div>
                            </Row>
                          </li>
                          <li>
                            <Row className='mb-3 pricing-features-item'>
                              <span>
                                <Icon name='checkmark-circle' fill='#F7D56E' />
                              </span>
                              <div className='ml-2'>
                                Onboarding & training
                              </div>
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

Payment.propTypes = {}
export const onPaymentLoad = () => {
  if (!Project.chargebee?.site) {
    return
  }
  const planId = API.getCookie('plan')
  let link
  if (planId && Utils.getFlagsmithHasFeature('payments_enabled')) {
    ;(function () {
      // Create a link element with data-cb-plan-id attribute
      link = document.createElement('a')
      link.setAttribute('data-cb-type', 'checkout')
      link.setAttribute('data-cb-plan-id', planId)
      link.setAttribute('href', 'javascript:void(0)')
      // Append the link to the body
      document.body.appendChild(link)
    })()
  }
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
  if (link) {
    link.click()
    document.body.removeChild(link)
    API.setCookie('plan', null)
  }
}

const WrappedPayment = makeAsyncScriptLoader(
  'https://js.chargebee.com/v2/chargebee.js',
  {
    removeOnUnmount: true,
  },
)(ConfigProvider(Payment))
export default (props) => (
  <WrappedPayment {...props} asyncScriptOnLoad={onPaymentLoad} />
)
