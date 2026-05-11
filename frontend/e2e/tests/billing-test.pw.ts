import { test, expect } from '../test-setup'
import { byId, log, createHelpers } from '../helpers'
import { E2E_BILLING_USER, PASSWORD } from '../config'

declare global {
  interface Window {
    __cbCheckoutClicks: Array<string | null>
  }
}

test.describe('Billing', () => {
  test('Free trial buttons stay wired after toggling between yearly and monthly @saas', async ({
    page,
  }) => {
    const { click, login, waitForElementVisible } = createHelpers(page)

    // Serve an empty Chargebee bundle so useScript resolves without pulling
    // the real library from Chargebee's CDN.
    await page.route('**/js.chargebee.com/**/chargebee.js*', (route) =>
      route.fulfill({
        body: '',
        contentType: 'application/javascript',
        status: 200,
      }),
    )

    // Stub window.Chargebee with a minimal implementation of the DOM-scan
    // contract: registerAgain() binds a click handler to every
    // [data-cb-type="checkout"] element that records the plan id.
    // This is what the real library does — we record instead of opening a
    // hosted checkout so the test can observe whether the button is wired.
    await page.addInitScript(() => {
      window.__cbCheckoutClicks = []
      const registerAgain = () => {
        document
          .querySelectorAll<HTMLElement>('[data-cb-type="checkout"]')
          .forEach((element) => {
            const marker = '__cbBound'
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            if ((element as any)[marker]) return
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            ;(element as any)[marker] = true
            element.addEventListener('click', (event) => {
              event.preventDefault()
              window.__cbCheckoutClicks.push(
                element.getAttribute('data-cb-plan-id'),
              )
            })
          })
      }
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(window as any).Chargebee = {
        getInstance: () => ({
          openCheckout: () => {},
          setCheckoutCallbacks: () => {},
        }),
        init: () => {},
        registerAgain,
      }
    })

    log('Login')
    await login(E2E_BILLING_USER, PASSWORD)

    log('Navigate to Billing tab')
    await waitForElementVisible(byId('organisation-link'))
    await click(byId('organisation-link'))
    await waitForElementVisible(byId('org-settings-link'))
    await click(byId('org-settings-link'))
    await click(byId('billing'))

    const getTrialButton = () =>
      page
        .locator('button[data-cb-type="checkout"]')
        .filter({ hasText: '14 Day Free Trial' })
        .first()
    const toggle = page.getByRole('switch').first()

    log('Confirm free-trial button is wired in yearly mode')
    const yearlyButton = getTrialButton()
    await yearlyButton.waitFor({ state: 'visible' })
    const yearlyPlanId = await yearlyButton.getAttribute('data-cb-plan-id')
    expect(yearlyPlanId).toBeTruthy()
    await yearlyButton.click()
    await expect
      .poll(() => page.evaluate(() => window.__cbCheckoutClicks))
      .toEqual([yearlyPlanId])

    log('Toggle to Monthly and click the free-trial button')
    await toggle.click()
    const monthlyButton = getTrialButton()
    await monthlyButton.waitFor({ state: 'visible' })
    const monthlyPlanId = await monthlyButton.getAttribute('data-cb-plan-id')
    expect(monthlyPlanId).toBeTruthy()
    expect(monthlyPlanId).not.toBe(yearlyPlanId)
    await monthlyButton.click()
    // Before the fix, registerAgain is not called after the toggle, so the
    // remounted button has no click handler and nothing is recorded.
    await expect
      .poll(() => page.evaluate(() => window.__cbCheckoutClicks))
      .toEqual([yearlyPlanId, monthlyPlanId])

    log('Toggle back to Yearly and click the free-trial button')
    await toggle.click()
    const yearlyButtonAgain = getTrialButton()
    await yearlyButtonAgain.waitFor({ state: 'visible' })
    expect(await yearlyButtonAgain.getAttribute('data-cb-plan-id')).toBe(
      yearlyPlanId,
    )
    await yearlyButtonAgain.click()
    await expect
      .poll(() => page.evaluate(() => window.__cbCheckoutClicks))
      .toEqual([yearlyPlanId, monthlyPlanId, yearlyPlanId])
  })
})
