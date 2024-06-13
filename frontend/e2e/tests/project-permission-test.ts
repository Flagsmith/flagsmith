import {
  byId,
  click,
  createFeature,
  createSegment,
  deleteFeature,
  gotoSegments,
  log,
  login,
  setText,
  toggleFeature,
  waitForElementVisible,
} from '../helpers.cafe'
import {
  PASSWORD,
  E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
} from '../config'
import { Selector, t } from 'testcafe'

export default async function () {
  log('Login')
  await login(E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS, PASSWORD)
  await click('#project-select-0')
  await t
    .expect(Selector('#project-select-1').exists)
    .notOk('The element"#project-select-1" should not be present')
  log('Create environment')
  await setText('[name="envName"]', 'Staging')
  await click('#create-env-btn')
  await waitForElementVisible(byId('switch-environment-staging-active'))
  log('Handle Features')
  await createFeature(0, 'test_feature', false)
  await toggleFeature(0, true)
  await t.eval(() => {
    window.scrollBy(0, 15000)
  })
  log('Delete Feature')
  await deleteFeature(0, 'test_feature')
  log('Manage Segments')
  await gotoSegments()
  // (=== 18 || === 19) && (> 17 || < 19) && (!=20) && (<=18) && (>=18)
  // Rule 1- Age === 18 || Age === 19

  await createSegment(0, '18_or_19', [
    // rule 2 =18 || =17
    {
      name: 'age',
      operator: 'EQUAL',
      ors: [
        {
          name: 'age',
          operator: 'EQUAL',
          value: 17,
        },
      ],
      value: 18,
    },
    // rule 2 >17 or <10
    {
      name: 'age',
      operator: 'GREATER_THAN',
      ors: [
        {
          name: 'age',
          operator: 'LESS_THAN',
          value: 10,
        },
      ],
      value: 17,
    },
    // rule 3 !=20
    {
      name: 'age',
      operator: 'NOT_EQUAL',
      value: 20,
    },
    // Rule 4 <= 18
    {
      name: 'age',
      operator: 'LESS_THAN_INCLUSIVE',
      value: 18,
    },
    // Rule 5 >= 18
    {
      name: 'age',
      operator: 'GREATER_THAN_INCLUSIVE',
      value: 18,
    },
  ])
}
