# Reporting Security Issues
ESModulesLinkingError: export 'toPath' (imported as 'toPath') was not found in 'unicorn-magic' (possible exports: delay) ╭─[13:33] 11 │ addExecPath = true, 12 │ } = {}) => { 13 │ const cwdPath = path.resolve(toPath(cwd)); · ────── 14 │ const result = []; 15 │ const pathParts = pathOption.split(path.delimiter); ╰──── × ESModulesLinkingError: export 'traversePathUp' (imported as 'traversePathUp') was not found in 'unicorn-magic' (possible exports: delay) ╭─[31:28] 29 │ 30 │ const applyPreferLocal = (result, pathParts, cwdPath) => { 31 │ for (const directory of traversePathUp(cwdPath)) { · ────────────── 32 │ const pathPart = path.join(directory, 'node_modules/.bin'); 33 │ if (!pathParts.includes(pathPart)) { ╰──── × ESModulesLinkingError: export 'toPath' (imported as 'toPath') was not found in 'unicorn-magic' (possible exports: delay) ╭─[41:43] 39 │ // Ensure the running `node` binary is used 40 │ const applyExecPath = (result, pathParts, execPath, cwdPath) => { 41 │ const pathPart = path.resolve(cwdPath, toPath(execPath), '..'); · ────── 42 │ if (!pathParts.includes(pathPart)) { 43 │ result.push(pathPart); ╰────
Recent searches
@ainetwork/adk-provider-memory-mongodb
@arnavvv/deppulse
Please report any security issues you discover to support[at]flagsmith[dot]com

We will assess the risk and, if required, take the following actions:

- Identify the remediation.
- Implement and deploy a fix to our SaaS platform, Docker images and source code.
- Create a GitHub issue, labelled `Security` where appropriate.

Thank you for your contribution.
