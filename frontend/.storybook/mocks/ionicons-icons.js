// Storybook mock for ionicons/icons.
// Real exports are SVG strings; for stories, the IonIcon mock just needs each
// import to resolve to *something*, so we proxy any property access to its
// own name. This lets `import { closeCircle, apps } from 'ionicons/icons'`
// resolve cleanly without listing every icon name.
const handler = {
  get: (_target, prop) => (typeof prop === 'string' ? prop : undefined),
}
const proxy = new Proxy({}, handler)

// Named imports webpack already saw in source files; ESM static analysis
// won't pick up Proxy access for named imports, so we re-export the most
// common ones explicitly. Add to this list as new IonIcon usages appear.
export const apps = 'apps'
export const checkmark = 'checkmark'
export const checkmarkCircle = 'checkmarkCircle'
export const chevronDown = 'chevronDown'
export const chevronForward = 'chevronForward'
export const chevronUp = 'chevronUp'
export const close = 'close'
export const closeCircle = 'closeCircle'
export const informationCircleOutline = 'informationCircleOutline'
export const statsChart = 'statsChart'

export default proxy
