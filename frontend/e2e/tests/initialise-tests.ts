import {
  byId,
  click,
  getFlagsmith,
  log,
  setText,
  waitForElementVisible,
} from '../helpers.cafe';
import { E2E_SIGN_UP_USER, PASSWORD } from '../config'

export default async function () {
  const flagsmith = await getFlagsmith()
  log('Create Organisation')
  await click(byId('jsSignup'))
  await setText(byId('firstName'), 'Bullet') // visit the url
  await setText(byId('lastName'), 'Train') // visit the url
  await setText(byId('email'), E2E_SIGN_UP_USER) // visit the url
  await setText(byId('password'), PASSWORD) // visit the url
  await click(byId('signup-btn'))
  await setText('[name="orgName"]', 'Flagsmith Ltd 0')
  await click('#create-org-btn')

  if(flagsmith.hasFeature("integration_onboarding")) {
    await click(byId("integration-0"))
    await click(byId("integration-1"))
    await click(byId("integration-2"))
    await click(byId("submit-integrations"))
  }
  await click(byId('create-project'))

  log('Create Project')
  await click(byId('create-first-project-btn'))
  await setText(byId('projectName'), 'My Test Project')
  await click(byId('create-project-btn'))
  await waitForElementVisible(byId('features-page'))

  log('Hide disabled flags')
  await click('#project-link')
  await click('#project-settings-link')
  await click(byId('js-sdk-settings'))
  await click(byId('js-hide-disabled-flags'))
  await setText(byId('js-project-name'), 'My Test Project')
  await click(byId('js-confirm'))
}
