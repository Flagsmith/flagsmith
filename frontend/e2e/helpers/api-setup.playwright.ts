import type { APIRequestContext } from '@playwright/test'
import { expect } from '@playwright/test'
import { E2E_USER, PASSWORD } from '../config'
import Project from '../../common/project'

type ApiList<T> = T[] | { results: T[] }

const unwrap = <T>(body: ApiList<T>): T[] =>
  Array.isArray(body) ? body : body.results

// A project of our own per test, so a run never races another test's data
// or an earlier iteration of the same test under `E2E_REPEAT`.
export const createProjectThroughApi = async (
  request: APIRequestContext,
  name: string,
) => {
  const api = Project.api

  const loginRes = await request.post(`${api}auth/login/`, {
    data: { email: E2E_USER, password: PASSWORD },
  })
  expect(loginRes.ok()).toBeTruthy()
  const { key } = await loginRes.json()
  const headers = { Authorization: `Token ${key}` }

  // The seeded organisation from e2e_seed_data.py; other orgs may appear
  // concurrently (e.g. the versioning test creates one), so match by name.
  const organisation = unwrap<{ id: number; name: string }>(
    await (await request.get(`${api}organisations/`, { headers })).json(),
  ).find((o) => o.name === 'Bullet Train Ltd')
  expect(organisation).toBeTruthy()

  // The seeded org is at its subscription's project cap; the E2E auth token
  // header marks the request as E2E so the cap check is bypassed.
  const e2eToken =
    process.env.E2E_TEST_TOKEN ??
    process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`] ??
    ''
  const projectRes = await request.post(`${api}projects/`, {
    data: { name, organisation: organisation?.id },
    headers: { ...headers, 'X-E2E-Test-Auth-Token': e2eToken.trim() },
  })
  expect(projectRes.ok()).toBeTruthy()
  const project = (await projectRes.json()) as { id: number; name: string }

  return { api, headers, project }
}

export const createEnvironmentThroughApi = async (
  request: APIRequestContext,
  headers: Record<string, string>,
  api: string,
  name: string,
  projectId: number,
) => {
  const res = await request.post(`${api}environments/`, {
    data: { name, project: projectId },
    headers,
  })
  expect(res.ok()).toBeTruthy()
  return (await res.json()) as { id: number; api_key: string; name: string }
}
