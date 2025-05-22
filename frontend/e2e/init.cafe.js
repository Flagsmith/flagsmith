import fetch from 'node-fetch'
import { test, fixture } from 'testcafe'
import { waitForReact } from 'testcafe-react-selectors'

import Project from '../common/project'
import { getLogger, log, logout, logResults } from './helpers.cafe'
import environmentTest from './tests/environment-test'
import inviteTest from './tests/invite-test'
import projectTest from './tests/project-test'
import { testSegment1, testSegment2, testSegment3 } from './tests/segment-test'
import initialiseTests from './tests/initialise-tests'
import flagTests from './tests/flag-tests'
import versioningTests from './tests/versioning-tests'
import organisationPermissionTest from './tests/organisation-permission-test'
import projectPermissionTest from './tests/project-permission-test'
import environmentPermissionTest from './tests/environment-permission-test'
import rolesTest from './tests/roles-test'

require('dotenv').config()

const url = `http://localhost:${process.env.PORT || 8080}/`
const e2eTestApi = `${process.env.FLAGSMITH_API_URL || Project.api}e2etests/teardown/`
const logger = getLogger()

console.log(
  '\n',
  '\x1b[32m',
  `E2E using API: ${e2eTestApi}. E2E URL: ${url}`,
  '\x1b[0m',
  '\n',
)

fixture`E2E Tests`.requestHooks(logger).before(async () => {
  const token = process.env.E2E_TEST_TOKEN
    ? process.env.E2E_TEST_TOKEN
    : process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`]

  if (token) {
    await fetch(e2eTestApi, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-E2E-Test-Auth-Token': token.trim(),
      },
      body: JSON.stringify({}),
    }).then((res) => {
      if (res.ok) {
        // eslint-disable-next-line no-console
        console.log(
          '\n',
          '\x1b[32m',
          'e2e teardown successful',
          '\x1b[0m',
          '\n',
        )
      } else {
        // eslint-disable-next-line no-console
        console.error(
          '\n',
          '\x1b[31m',
          'e2e teardown failed',
          res.status,
          '\x1b[0m',
          '\n',
        )
      }
      console.log('Starting E2E tests')
    })
  } else {
    // eslint-disable-next-line no-console
    console.error(
      '\n',
      '\x1b[31m',
      'e2e teardown failed - no available token',
      '\x1b[0m',
      '\n',
    )
  }
}).page`${url}`
  .beforeEach(async () => {
    await waitForReact()
  })
  .afterEach(async (t) => {
    if (t.test.meta.autoLogout) {
      log('Log out')
      await logout()
    }
    await logResults(logger.requests, t)
  })

test('Segment-part-1', testSegment1).meta({ autoLogout: true, category: 'oss' })

test('Segment-part-2', testSegment2).meta({ autoLogout: true, category: 'oss' })

test('Segment-part-3', testSegment3).meta({ autoLogout: true, category: 'oss' })

test('Flag', flagTests).meta({ autoLogout: true, category: 'oss' })

test('Signup', initialiseTests).meta({ autoLogout: true, category: 'oss' })

test('Invite', inviteTest).meta({ category: 'oss' })

test('Environment', environmentTest).meta({ autoLogout: true, category: 'oss' })

test('Project', projectTest).meta({ autoLogout: true, category: 'oss' })

test('Versioning', versioningTests).meta({ autoLogout: true, category: 'oss' })

test('Organisation-permission', organisationPermissionTest).meta({ autoLogout: true, category: 'enterprise' })

test('Project-permission', projectPermissionTest).meta({ autoLogout: true, category: 'enterprise' })

test('Environment-permission', environmentPermissionTest).meta({ autoLogout: true, category: 'enterprise' })

test('Roles', rolesTest).meta({ autoLogout: true, category: 'enterprise' })
