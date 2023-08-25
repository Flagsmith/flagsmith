import fetch from 'node-fetch'
import { t, test } from 'testcafe'
import { waitForReact } from 'testcafe-react-selectors'

import Project from '../common/project'
import { getLogger, log, logout, logResults } from './helpers.cafe'
import environmentTest from './tests/environment-test'
import inviteTest from './tests/invite-test'
import projectTest from './tests/project-test'
import segmentTest from './tests/segment-test'
import initialiseTests from './tests/initialise-tests'
import flagTests from './tests/flag-tests'

require('dotenv').config()

const url = `http://localhost:${process.env.PORT || 8080}/`
const logger = getLogger()
let e2eInitDone = undefined

fixture`E2E Tests`.requestHooks(logger).before(async () => {
  const token = process.env.E2E_TEST_TOKEN
    ? process.env.E2E_TEST_TOKEN
    : process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`]

  if (token) {
    await fetch(`${Project.api}e2etests/teardown/`, {
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
  .after(async (t) => {
    console.log('Start of Initialise Requests')
    await logResults(logger.requests, t)
    console.log('End of Initialise Requests')
  })

const waitForInitTests = async () => {
  log('Waiting for the initialization', 'Environment Test')
  while (e2eInitDone === undefined) {
    await t.wait(100)
  }
}

test('[Initialise]', async () => {
  console.log('Init')
  await initialiseTests()
  await logout()
  e2eInitDone = true
}).after(async () => {
  if (!e2eInitDone) {
    e2eInitDone = false
    throw new Error('not passed')
  }
})

test('[Flag Tests]', async () => {
  await waitForInitTests()
  await flagTests()
  await logout()
})

test('[Segment Tests]', async () => {
  await waitForInitTests()
  await segmentTest()
  await logout()
})

test('[Environment Tests]', async () => {
  await waitForInitTests()
  await environmentTest()
  await logout()
  await inviteTest()
  await logout()
})

test('[Project Tests]', async () => {
  await waitForInitTests()
  await projectTest()
  await logout()
})
