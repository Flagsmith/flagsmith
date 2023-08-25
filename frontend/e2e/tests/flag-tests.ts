import {
  assertTextContent,
  byId,
  click,
  closeModal,
  createFeature,
  createRemoteConfig,
  deleteFeature,
  getText,
  log,
  login,
  setText,
  toggleFeature,
  waitForElementVisible,
} from '../helpers.cafe'
import { t } from 'testcafe'

const email = 'nightwatch@solidstategroup.com'
const password = 'str0ngp4ssw0rd!'

export default async function () {
  log('Login');
  await login(email, password);
  await click('#project-select-0');

  log('Create Features')
  await click('#features-link')

  await createRemoteConfig(0, 'header_size', 'big')
  await createRemoteConfig(0, 'mv_flag', 'big', null, null, [
    { value: 'medium', weight: 100 },
    { value: 'small', weight: 0 },
  ])
  await createFeature(1, 'header_enabled', false)

  log('Create Short Life Feature')
  await createFeature(3, 'short_life_feature', false)
  await deleteFeature(3, 'short_life_feature')

  log('Toggle Feature')
  await toggleFeature(0, true)

  log('Try it')
  await t.wait(2000)
  await click('#try-it-btn')
  await t.wait(1500)
  let text = await getText('#try-it-results')
  let json
  try {
    json = JSON.parse(text)
  } catch (e) {
    throw new Error('Try it results are not valid JSON')
  }
  await t.expect(json.header_size.value).eql('big')
  await t.expect(json.mv_flag.value).eql('big')
  await t.expect(json.header_enabled.enabled).eql(true)

  log('Update feature')
  await click(byId('feature-item-1'))
  await setText(byId('featureValue'), '12')
  await click('#update-feature-btn')
  await assertTextContent(byId('feature-value-1'), '12')
  await t.pressKey('esc')
  await closeModal()

  log('Try it again')
  await t.wait(2000)
  await click('#try-it-btn')
  await t.wait(1500)
  text = await getText('#try-it-results')
  try {
    json = JSON.parse(text)
  } catch (e) {
    throw new Error('Try it results are not valid JSON')
  }
  await t.expect(json.header_size.value).eql(12)

  log('Change feature value to boolean')
  await click(byId('feature-item-1'))
  await setText(byId('featureValue'), 'false')
  await click('#update-feature-btn')
  await assertTextContent(byId('feature-value-1'), 'false')
  await closeModal()

  log('Try it again 2')
  await t.wait(2000)
  await click('#try-it-btn')
  await t.wait(1500)
  text = await getText('#try-it-results')
  try {
    json = JSON.parse(text)
  } catch (e) {
    throw new Error('Try it results are not valid JSON')
  }
  await t.expect(json.header_size.value).eql(false)

  log('Switch environment')
  await click(byId('switch-environment-production'))

  log('Feature should be off under different environment')
  await waitForElementVisible(byId('switch-environment-production-active'))
  await waitForElementVisible(byId('feature-switch-0-off'))

  log('Clear down features')
  await deleteFeature(1, 'header_size')
  await deleteFeature(0, 'header_enabled')

}
