import React from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
// @ts-ignore
import AccountProvider from 'common/providers/AccountProvider'
import { Organisation } from 'common/types/responses'
import Payment from './modals/payment'
import BlockedOrgInfo from './BlockedOrgInfo'

const Blocked = () => (
  <div className='fullscreen-container maintenance fullscreen-container__grey justify-content-center dark'>
    {!Utils.isSaas() ? (
      <div className='col-md-6 mt-5' id='sign-up'>
        <h1>Please get in touch</h1>
        <span className='h4'>
          Your organisation has been disabled. Please contact Flagsmith support
          at{' '}
          <a
            target='_blank'
            href='mailto:support@flagsmith.com'
            rel='noreferrer'
          >
            support@flagsmith.com
          </a>
          .
        </span>
        <BlockedOrgInfo />
      </div>
    ) : (
      <div className='col-md-8 mt-5' id='sign-up'>
        <AccountProvider>
          {({ organisation }: { organisation: Organisation | null }) =>
            organisation ? (
              <Payment
                organisation={organisation}
                isDisableAccountText='Your organisation has been disabled. Please upgrade your plan or contact us:'
              />
            ) : null
          }
        </AccountProvider>
      </div>
    )}
  </div>
)

export default ConfigProvider(Blocked)
