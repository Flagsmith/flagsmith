import {
  byId,
  click,
  closeModal,
  createFeature,
  createRemoteConfig,
  deleteFeature,
  editRemoteConfig,
  gotoFeatures,
  log,
  login,
  parseTryItResults,
  toggleFeature,
  waitForElementVisible,
} from '../helpers.cafe'
import { t } from 'testcafe'
import { E2E_USER, PASSWORD } from '../config'

export default async function () {
  log('Login')
  await login(E2E_USER, PASSWORD)
  await click('#project-select-0')

  log('Go to features')
  await waitForElementVisible('#features-link')
  await click('#features-link')

  await createRemoteConfig(0, 'header_size', 'big')
  await createRemoteConfig(0, 'mv_flag', 'big', null, null, [
    { value: 'medium', weight: 100 },
    { value: 'small', weight: 0 },
  ])
  await createFeature(1, 'header_enabled', false)

  log('Create Short Life Feature')
  await createFeature(3, 'short_life_feature', false)
  await t.eval(() => {
    window.scrollBy(0, 15000)
  })

  log('Delete Short Life Feature')
  await deleteFeature(3, 'short_life_feature')
  await t.eval(() => {
    window.scrollBy(0, 30000)
  })

  log('Toggle Feature')
  await toggleFeature(0, true)

  log('Try it')
  await t.wait(2000)
  await click('#try-it-btn')
  await t.wait(500)
  let json = await parseTryItResults()
  await t.expect(json.header_size.value).eql('big')
  await t.expect(json.mv_flag.value).eql('big')
  await t.expect(json.header_enabled.enabled).eql(true)

  log('Update feature')
  await editRemoteConfig(1, 12)

  log('Try it again')
  await t.wait(500)
  await click('#try-it-btn')
  await t.wait(500)
  json = await parseTryItResults()
  await t.expect(json.header_size.value).eql(12)

  log('Change feature value to boolean')
  await editRemoteConfig(1, false)

  log('Try it again 2')
  await t.wait(2000)
  await click('#try-it-btn')
  await t.wait(500)
  json = await parseTryItResults()
  await t.expect(json.header_size.value).eql(false)

  log('Switch environment')
  await click(byId('switch-environment-production'))

  log('Feature should be off under different environment')
  await waitForElementVisible(byId('switch-environment-production-active'))
  await waitForElementVisible(byId('feature-switch-0-off'))

  log('Switch back to Development environment')
  await click(byId('switch-environment-development'))
  await waitForElementVisible(byId('switch-environment-development-active'))

  log('Clear down features')
  await deleteFeature(1, 'header_size')
  await deleteFeature(0, 'header_enabled')
  await deleteFeature(0, 'mv_flag')

  log('Create multivariate feature for toggle test')
  await createRemoteConfig(
    0,
    'mv_toggle_test',
    'control',
    'MV toggle test',
    false,
    [
      { value: 'variant_a', weight: 50 },
      { value: 'variant_b', weight: 50 },
    ],
  )

  log('Toggle multivariate feature via edit modal')
  await gotoFeatures()
  await click(byId('feature-switch-0-on'))
  await waitForElementVisible('#create-feature-modal')
  await click(byId('toggle-feature-button'))
  await click(byId('update-feature-btn'))
  await closeModal()
  await waitForElementVisible(byId('feature-switch-0-off'))

  log('Multivariate toggle test via modal passed')

  log('Toggle multivariate feature on again via list click (tests 400 error fix)')
  // This tests the fix for the 400 error when toggling MV features
  // Clicking toggle on MV feature opens the edit modal
  // The fix includes multivariate_feature_state_values in the PATCH payload
  await click(byId('feature-switch-0-off'))
  await waitForElementVisible('#create-feature-modal')
  await click(byId('toggle-feature-button'))
  await click(byId('update-feature-btn'))
  await closeModal()
  await waitForElementVisible(byId('feature-switch-0-on'))

  log('Toggle MV feature off again via list click')
  await click(byId('feature-switch-0-on'))
  await waitForElementVisible('#create-feature-modal')
  await click(byId('toggle-feature-button'))
  await click(byId('update-feature-btn'))
  await closeModal()
  await waitForElementVisible(byId('feature-switch-0-off'))

  log('Multivariate toggle from list test passed')
  await deleteFeature(0, 'mv_toggle_test')
}
