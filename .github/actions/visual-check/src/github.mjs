// @ts-check
import fs from 'node:fs'

/**
 * @typedef {{ token: string, apiUrl: string, serverUrl: string, repository: string }} GitHubContext
 * @typedef {{ path: string, file: string }} Upload
 */

export class GitHubError extends Error {
  /** @param {number} status @param {string} message */
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

/**
 * @param {GitHubContext} context
 * @param {string} method
 * @param {string} route
 * @param {unknown} [body]
 * @returns {Promise<any>}
 */
export const request = async (context, method, route, body) => {
  const response = await fetch(`${context.apiUrl}${route}`, {
    body: body === undefined ? undefined : JSON.stringify(body),
    headers: {
      'Accept': 'application/vnd.github+json',
      'Authorization': `Bearer ${context.token}`,
      'Content-Type': 'application/json',
      'X-GitHub-Api-Version': '2022-11-28',
    },
    method,
  })
  if (!response.ok) {
    throw new GitHubError(
      response.status,
      `${method} ${route} failed with ${response.status}: ${await response.text()}`,
    )
  }
  return response.status === 204 ? undefined : response.json()
}

/** @param {GitHubContext} context @param {string} branch */
const getBranchHead = async (context, branch) => {
  try {
    const ref = await request(
      context,
      'GET',
      `/repos/${context.repository}/git/ref/heads/${branch}`,
    )
    return /** @type {string} */ (ref.object.sha)
  } catch (error) {
    if (error instanceof GitHubError && error.status === 404) return undefined
    throw error
  }
}

/**
 * Raw URL GitHub can render in markdown. Pinned to the commit so a later
 * clean-up of the branch can't swap what an old check shows.
 *
 * @param {GitHubContext} context
 * @param {string} commit
 * @param {string} file
 */
export const rawUrl = (context, commit, file) =>
  context.serverUrl === 'https://github.com'
    ? `https://raw.githubusercontent.com/${context.repository}/${commit}/${file}`
    : `${context.serverUrl}/${context.repository}/raw/${commit}/${file}`

/**
 * Commits the files to `branch` on top of its current head, creating the
 * branch if needed. Retries when another run moved the branch in between.
 *
 * @param {GitHubContext} context
 * @param {string} branch
 * @param {Upload[]} uploads
 * @param {string} message
 * @returns {Promise<string>} the commit SHA
 */
export const commitFiles = async (context, branch, uploads, message) => {
  const repo = `/repos/${context.repository}`
  const tree = []
  for (const upload of uploads) {
    const blob = await request(context, 'POST', `${repo}/git/blobs`, {
      content: fs.readFileSync(upload.file).toString('base64'),
      encoding: 'base64',
    })
    tree.push({ mode: '100644', path: upload.path, sha: blob.sha, type: 'blob' })
  }

  for (let attempt = 1; ; attempt++) {
    const head = await getBranchHead(context, branch)
    const baseTree = head
      ? (await request(context, 'GET', `${repo}/git/commits/${head}`)).tree.sha
      : undefined
    const newTree = await request(context, 'POST', `${repo}/git/trees`, {
      base_tree: baseTree,
      tree,
    })
    const commit = await request(context, 'POST', `${repo}/git/commits`, {
      message,
      parents: head ? [head] : [],
      tree: newTree.sha,
    })
    try {
      if (head) {
        await request(context, 'PATCH', `${repo}/git/refs/heads/${branch}`, {
          force: false,
          sha: commit.sha,
        })
      } else {
        await request(context, 'POST', `${repo}/git/refs`, {
          ref: `refs/heads/${branch}`,
          sha: commit.sha,
        })
      }
      return commit.sha
    } catch (error) {
      const raced = error instanceof GitHubError && error.status === 422
      if (!raced || attempt >= 3) throw error
    }
  }
}

/**
 * Rewrites `branch` as a single parentless commit holding only the paths
 * `keep` accepts, so old images drop out of the history too. Deletes the
 * branch when nothing is left.
 *
 * @param {GitHubContext} context
 * @param {string} branch
 * @param {(path: string) => boolean} keep
 * @returns {Promise<{ kept: number, removed: number }>}
 */
export const pruneBranch = async (context, branch, keep) => {
  const repo = `/repos/${context.repository}`
  const head = await getBranchHead(context, branch)
  if (!head) return { kept: 0, removed: 0 }

  const commit = await request(context, 'GET', `${repo}/git/commits/${head}`)
  const listing = await request(
    context,
    'GET',
    `${repo}/git/trees/${commit.tree.sha}?recursive=1`,
  )
  if (listing.truncated) {
    throw new Error(`The ${branch} tree is too large to list; prune it by hand.`)
  }

  /** @type {{ path: string, mode: string, type: string, sha: string }[]} */
  const blobs = listing.tree.filter(
    (/** @type {{ type: string }} */ entry) => entry.type === 'blob',
  )
  const kept = blobs.filter((entry) => keep(entry.path))
  const removed = blobs.length - kept.length
  if (!removed) return { kept: kept.length, removed }

  if (!kept.length) {
    await request(context, 'DELETE', `${repo}/git/refs/heads/${branch}`)
    return { kept: 0, removed }
  }

  const tree = await request(context, 'POST', `${repo}/git/trees`, {
    tree: kept.map(({ mode, path, sha, type }) => ({ mode, path, sha, type })),
  })
  const squashed = await request(context, 'POST', `${repo}/git/commits`, {
    message: 'Prune visual check images',
    parents: [],
    tree: tree.sha,
  })
  await request(context, 'PATCH', `${repo}/git/refs/heads/${branch}`, {
    force: true,
    sha: squashed.sha,
  })
  return { kept: kept.length, removed }
}

/** @param {GitHubContext} context @returns {Promise<number[]>} */
export const listOpenPullRequests = async (context) => {
  /** @type {number[]} */
  const numbers = []
  for (let page = 1; ; page++) {
    const pulls = await request(
      context,
      'GET',
      `/repos/${context.repository}/pulls?state=open&per_page=100&page=${page}`,
    )
    numbers.push(...pulls.map((/** @type {{ number: number }} */ pull) => pull.number))
    if (pulls.length < 100) return numbers
  }
}

/**
 * @param {GitHubContext} context
 * @param {{ name: string, headSha: string, conclusion: string, detailsUrl?: string, output: { title: string, summary: string, text: string } }} check
 * @returns {Promise<string>} the check's HTML URL
 */
export const createCheckRun = async (context, check) => {
  const created = await request(
    context,
    'POST',
    `/repos/${context.repository}/check-runs`,
    {
      conclusion: check.conclusion,
      details_url: check.detailsUrl,
      head_sha: check.headSha,
      name: check.name,
      output: check.output,
      status: 'completed',
    },
  )
  return created.html_url
}
