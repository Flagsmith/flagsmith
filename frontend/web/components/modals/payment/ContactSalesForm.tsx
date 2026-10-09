import React, { FC, useEffect } from 'react'
import { useScript } from 'common/hooks/useScript'
import AccountStore from 'common/stores/account-store'
import { AccountModel } from 'common/types/responses'
import {
  CONTACT_SALES_FORM,
  CONTACT_SALES_URL,
  HUBSPOT_FORMS_SCRIPT_URL,
} from './constants'

// HubSpot passes a jQuery object when jQuery is on the page, as it is here.
type HubSpotFormArg = HTMLFormElement | { jquery: string; 0: HTMLFormElement }

type HubSpotFormOptions = typeof CONTACT_SALES_FORM & {
  target: string
  onFormReady: (form: HubSpotFormArg) => void
}

declare global {
  interface Window {
    hbspt?: { forms: { create: (options: HubSpotFormOptions) => void } }
  }
}

const TARGET_ID = 'contact-sales-form'

// The form renders in an iframe, so set values the way HubSpot documents:
// assign, then fire an input event so the form registers them.
const prefill = (arg: HubSpotFormArg) => {
  const form = 'jquery' in arg ? arg[0] : arg
  const user = AccountStore.getUser() as AccountModel | undefined
  if (!form || !user) return
  const values: Record<string, string | undefined> = {
    email: user.email,
    firstname: user.first_name,
    lastname: user.last_name,
  }
  Object.entries(values).forEach(([name, value]) => {
    const input = form.querySelector<HTMLInputElement>(`input[name="${name}"]`)
    if (!input || !value) return
    input.value = value
    input.dispatchEvent(new Event('input', { bubbles: true }))
  })
}

const ContactSalesForm: FC = () => {
  const { error, ready } = useScript(HUBSPOT_FORMS_SCRIPT_URL)

  useEffect(() => {
    if (ready && window.hbspt) {
      window.hbspt.forms.create({
        ...CONTACT_SALES_FORM,
        onFormReady: prefill,
        target: `#${TARGET_ID}`,
      })
    }
  }, [ready])

  // Ad blockers commonly block HubSpot, so always leave a way through.
  if (error || (ready && !window.hbspt)) {
    return (
      <div className='p-4'>
        We couldn't load the form here. Please{' '}
        <a href={CONTACT_SALES_URL} target='_blank' rel='noreferrer'>
          contact us on our website
        </a>
        .
      </div>
    )
  }

  // HubSpot styles the form itself (dark labels), so it sits on a white
  // card to stay readable in dark mode.
  return (
    <div className='p-4'>
      <div className='bg-white rounded p-3'>
        <div id={TARGET_ID} />
      </div>
    </div>
  )
}

export default ContactSalesForm
