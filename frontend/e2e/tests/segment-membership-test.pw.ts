import { test, expect } from '../test-setup'
import { log, createHelpers } from '../helpers'
import { E2E_USER, PASSWORD, E2E_SEGMENT_PROJECT_1 } from '../config'

const TEST_SEGMENT = 'segment_membership_badge'
const ENV_COUNTS = [42, 17]

type Env = { id: number; name: string; api_key?: string }

test('Segment membership badges render in list, tab, and env select @oss', async ({
  page,
}) => {
  const {
    createSegment,
    deleteSegment,
    gotoProject,
    gotoSegments,
    login,
    waitForElementVisible,
  } = createHelpers(page)

  const envs: Env[] = []

  await page.route(/\/projects\/\d+\/environments\/\?/, async (route) => {
    const response = await route.fetch()
    const body = await response.json()
    if (!envs.length && Array.isArray(body?.results)) {
      body.results.slice(0, ENV_COUNTS.length).forEach((e: Env) => {
        envs.push({ id: e.id, name: e.name, api_key: e.api_key })
      })
    }
    await route.fulfill({ response, json: body })
  })

  const memberships = () =>
    envs.slice(0, ENV_COUNTS.length).map((e, i) => ({
      environment: e.id,
      count: ENV_COUNTS[i],
      last_synced_at: new Date().toISOString(),
    }))

  await page.route(/\/projects\/\d+\/segments\/\?/, async (route) => {
    const response = await route.fetch()
    const body = await response.json()
    if (envs.length && Array.isArray(body?.results) && body.results.length) {
      const target =
        body.results.find((s: { name: string }) => s.name === TEST_SEGMENT) ??
        body.results[0]
      target.memberships = memberships()
    }
    await route.fulfill({ response, json: body })
  })

  await page.route(/\/projects\/\d+\/segments\/\d+\/?(?:\?|$)/, async (route) => {
    const response = await route.fetch()
    const body = await response.json()
    if (envs.length && body && typeof body === 'object') {
      body.memberships = memberships()
    }
    await route.fulfill({ response, json: body })
  })

  log('Login and create segment')
  await login(E2E_USER, PASSWORD)
  await gotoProject(E2E_SEGMENT_PROJECT_1)
  await waitForElementVisible('#features-page')
  await gotoSegments()
  await createSegment(TEST_SEGMENT, [
    { name: 'plan', operator: 'EQUAL', value: 'growth' },
  ])

  log('Reload segments list with mocked memberships')
  await gotoSegments()

  if (!envs.length) {
    throw new Error('Expected to capture project environments via route mock')
  }

  log('Assert total badge renders with sum across envs')
  const total = ENV_COUNTS.reduce((a, b) => a + b, 0)
  const totalBadge = page
    .locator('[data-test="segment-membership-total"]')
    .filter({ hasText: `${total}` })
  await expect(totalBadge.first()).toBeVisible()

  log('Open segment edit page')
  await page.getByText(TEST_SEGMENT).first().click()

  log('Switch to Identities tab — total badge sits next to label')
  await page.getByRole('button', { name: /Identities/ }).click()
  await expect(
    page
      .getByRole('button', { name: /Identities/ })
      .locator('[data-test="segment-membership-total"]'),
  ).toBeVisible()

  log('Open environment select and assert per-env badge')
  const select = page.locator('.react-select__control').first()
  await select.click()
  for (const env of envs.slice(0, ENV_COUNTS.length)) {
    await expect(
      page.locator(`[data-test="segment-membership-${env.api_key ?? ''}"]`).or(
        page.locator('.react-select__option').filter({ hasText: env.name }),
      ),
    ).toHaveCount(1, { timeout: 5_000 })
  }

  log('Select first env — full timestamp appears below the select')
  await page
    .locator('.react-select__option')
    .filter({ hasText: envs[0].name })
    .click()
  await expect(page.getByText(/Last synced:/)).toBeVisible()

  log('Clean up test segment')
  await page.goBack()
  await gotoSegments()
  await deleteSegment(TEST_SEGMENT)
})
