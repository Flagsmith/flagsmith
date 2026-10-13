import React, { FC, useEffect, useState } from 'react'
import Loader from 'components/Loader'
import { useScript } from 'common/hooks/useScript'
import AccountStore from 'common/stores/account-store'
import Project from 'common/project'
import { AccountModel } from 'common/types/responses'
import { CONTACT_SALES_URL, HUBSPOT_FORMS_SCRIPT_URL } from './constants'

// Set in env/project_prod.js only, so other environments get the website link.
type HubSpotFormConfig = { formId: string; portalId: string; region: string }

// HubSpot passes a jQuery object when jQuery is on the page, as it is here.
type HubSpotFormArg = HTMLFormElement | { jquery: string; 0: HTMLFormElement }

type HubSpotFormOptions = HubSpotFormConfig & {
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
const prefill = (form: HTMLFormElement) => {
  const user = AccountStore.getUser() as AccountModel | undefined
  if (!user) return
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

const WebsiteLink: FC = () => (
  <div className='p-4'>
    We couldn't load the form here. Please{' '}
    <a href={CONTACT_SALES_URL} target='_blank' rel='noreferrer'>
      contact us on our website
    </a>
    .
  </div>
)

const HubSpotForm: FC<{ config: HubSpotFormConfig }> = ({ config }) => {
  const { error, ready } = useScript(HUBSPOT_FORMS_SCRIPT_URL)
  const [form, setForm] = useState<HTMLFormElement | null>(null)

  useEffect(() => {
    if (ready && window.hbspt) {
      window.hbspt.forms.create({
        ...config,
        onFormReady: (arg) => {
          const element = ('jquery' in arg ? arg[0] : arg) as
            | HTMLFormElement
            | undefined
          if (!element) return
          prefill(element)
          setForm(element)
        },
        target: `#${TARGET_ID}`,
      })
    }
  }, [ready, config])

  // Ad blockers commonly block HubSpot, so always leave a way through.
  if (error || (ready && !window.hbspt)) {
    return <WebsiteLink />
  }

  // HubSpot styles the form itself (dark labels), so it sits on a white
  // card to stay readable in dark mode.
  return (
    <div className='p-4'>
      <div className='bg-white rounded p-3'>
        {!form && <Loader />}
        <div id={TARGET_ID} />
      </div>
    </div>
  )
}

const ContactSalesForm: FC = () => {
  const config: HubSpotFormConfig | undefined = Project.hubspotContactSalesForm
  return config ? <HubSpotForm config={config} /> : <WebsiteLink />
}

export default ContactSalesForm
