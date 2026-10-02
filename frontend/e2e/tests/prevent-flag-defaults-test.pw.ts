import { test, expect } from '../test-setup'
import { byId, log, createHelpers, visualSnapshot } from '../helpers'
import { E2E_USER, PASSWORD } from '../config'

test.describe('Prevent Flag Defaults', () => {
  test('Initial state and value are locked while variations stay editable @oss', async ({
    page,
  }, testInfo) => {
    const {
      click,
      featureValueField,
      login,
      setText,
      variationValueField,
      waitForElementVisible,
      waitForToast,
    } = createHelpers(page)

    log('Login')
    await login(E2E_USER, PASSWORD)

    // Its own project, so the setting never leaks into another test.
    log('Create test project')
    await click('.btn-project-create')
    await waitForElementVisible(byId('projectName'))
    await setText(byId('projectName'), 'Prevent Flag Defaults Test')
    await click(byId('create-project-btn'))
    await waitForElementVisible(byId('features-page'))

    log('Turn on prevent flag defaults')
    await click('#project-settings-link')
    await waitForElementVisible(byId('js-prevent-flag-defaults'))
    await click(byId('js-prevent-flag-defaults'))
    await waitForToast()

    log('Open the create feature modal')
    await click('#features-link')
    await waitForElementVisible(byId('show-create-feature-btn'))
    await click('#show-create-feature-btn')
    await waitForElementVisible(byId('featureID'))

    log('The two controls the API discards are locked')
    await expect(page.locator(byId('toggle-feature-button'))).toBeDisabled()
    // ValueEditor is a contenteditable <code>, not a form control, so
    // toBeDisabled() does not apply. These are what it actually sets.
    await expect(featureValueField()).toHaveAttribute('aria-readonly', 'true')
    await expect(featureValueField()).toHaveAttribute(
      'contenteditable',
      'false',
    )

    log('Everything the API keeps stays editable')
    await expect(page.locator(byId('featureID'))).toBeEnabled()
    await expect(page.locator(byId('featureDesc'))).toBeEnabled()

    // The reason this is not just isDisabled: the setting does not clear
    // variations, so locking them too would discard work it never touches.
    log('Variations stay editable')
    await click(byId('add-variation'))
    await waitForElementVisible(variationValueField(0))
    await expect(variationValueField(0)).toHaveAttribute(
      'contenteditable',
      'true',
    )
    await expect(page.locator(byId('add-variation'))).toBeEnabled()

    await visualSnapshot(page, 'prevent-flag-defaults-modal', testInfo)
  })
})
