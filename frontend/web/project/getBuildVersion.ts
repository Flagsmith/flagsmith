import { Version } from 'common/types/responses'

const _data = require('common/data/base/_data')
import Project from 'common/project'
let promise: Promise<Version>
// Allow promise to be undefined initially
let promise: Promise<Version> | undefined

export default function getVersion(force?: boolean): Promise<Version> {
  if (force || !promise) {
    promise = Promise.all([
      // Cast to Version["frontend"] to ensure the type fits our interface
      _data.get('/version').catch(() => ({} as Version['frontend'])),
      // Cast to Version["backend"] to ensure the type fits our interface
      _data
        .get(`${Project.api.replace('api/v1/', '')}version`)
        .catch(() => ({} as Version['backend'])),
    ]).then(([frontend, backend]) => {
      // Use default values if the properties are missing
      const tag = backend?.image_tag || 'Unknown'
      const backend_sha = backend?.ci_commit_sha || 'Unknown'
      const frontend_sha = frontend?.ci_commit_sha || 'Unknown'

      // Create the result ensuring it conforms to the Version type
      const res: Version = {
        backend,
        backend_sha,
        frontend,
        frontend_sha,
        tag,
      }

      // Make the version globally accessible as before
      global.flagsmithVersion = res
      return res
    })
  }
  return promise
}
