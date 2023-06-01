import AccountStore from 'common/stores/account-store'
import ProjectStore from 'common/stores/project-store'
import Project from 'common/project'
import {
  FeatureState,
  FeatureStateValue,
  FlagsmithValue,
  MultivariateFeatureStateValue,
  MultivariateOption,
  Project as ProjectType,
  ProjectFlag,
  SegmentCondition,
} from 'common/types/responses'
import flagsmith from 'flagsmith'
import { ReactNode } from 'react'
import _ from 'lodash'

const semver = require('semver')

const planNames = {
  enterprise: 'Enterprise',
  free: 'Free',
  scaleUp: 'Scale-Up',
  sideProject: 'Side Project',
  startup: 'Startup',
}
const Utils = Object.assign({}, require('./base/_utils'), {
  appendImage: (src: string) => {
    const img = document.createElement('img')
    img.src = src
    document.body.appendChild(img)
  },

  calculateControl(
    multivariateOptions: MultivariateOption[],
    variations?: MultivariateFeatureStateValue[],
  ) {
    if (!multivariateOptions || !multivariateOptions.length) {
      return 100
    }
    let total = 0
    multivariateOptions.map((v) => {
      const variation =
        variations &&
        variations.find((env) => env.multivariate_feature_option === v.id)
      total += variation
        ? variation.percentage_allocation
        : typeof v.default_percentage_allocation === 'number'
        ? v.default_percentage_allocation
        : (v as any).percentage_allocation
      return null
    })
    return 100 - total
  },

  changeRequestsEnabled(value: number | null | undefined) {
    return typeof value === 'number'
  },

  escapeHtml(html: string) {
    const text = document.createTextNode(html)
    const p = document.createElement('p')
    p.appendChild(text)
    return p.innerHTML
  },
  featureStateToValue(featureState: FeatureStateValue) {
    if (!featureState) {
      return null
    }

    if (typeof featureState.integer_value === 'number') {
      return Utils.getTypedValue(featureState.integer_value)
    }
    if (typeof featureState.float_value === 'number') {
      return Utils.getTypedValue(featureState.float_value)
    }

    return Utils.getTypedValue(
      featureState.string_value || featureState.boolean_value,
    )
  },
  findOperator(
    operator: SegmentCondition['operator'],
    value: string,
    conditions: SegmentCondition[],
  ) {
    const findAppended = `${value}`.includes(':')
      ? (conditions || []).find((v) => {
          const split = value.split(':')
          const targetKey = `:${split[split.length - 1]}`
          return v.value === operator + targetKey
        })
      : false
    if (findAppended) return findAppended

    return conditions.find((v) => v.value === operator)
  },
  getApproveChangeRequestPermission() {
    return 'APPROVE_CHANGE_REQUEST'
  },
  getFeatureStatesEndpoint(_project: ProjectType) {
    const project = _project || ProjectStore.model
    if (
      Utils.getFlagsmithHasFeature('edge_identities') &&
      project &&
      project.use_edge_identities
    ) {
      return 'edge-featurestates'
    }
    return 'featurestates'
  },
  getFlagValue(
    projectFlag: ProjectFlag,
    environmentFlag: FeatureState,
    identityFlag: FeatureState,
    multivariate_options: MultivariateFeatureStateValue[],
  ) {
    if (!environmentFlag) {
      return {
        description: projectFlag.description,
        enabled: false,
        feature_state_value: projectFlag.initial_value,
        hide_from_client: false,
        is_archived: projectFlag.is_archived,
        is_server_key_only: projectFlag.is_server_key_only,
        multivariate_options: projectFlag.multivariate_options,
        name: projectFlag.name,
        tags: projectFlag.tags,
        type: projectFlag.type,
      }
    }
    if (identityFlag) {
      return {
        description: projectFlag.description,
        enabled: identityFlag.enabled,
        feature_state_value: identityFlag.feature_state_value,
        hide_from_client: environmentFlag.hide_from_client,
        is_archived: projectFlag.is_archived,
        is_server_key_only: projectFlag.is_server_key_only,
        multivariate_options: projectFlag.multivariate_options,
        name: projectFlag.name,
        type: projectFlag.type,
      }
    }
    return {
      description: projectFlag.description,
      enabled: environmentFlag.enabled,
      feature_state_value: environmentFlag.feature_state_value,
      hide_from_client: environmentFlag.hide_from_client,
      is_archived: projectFlag.is_archived,
      is_server_key_only: projectFlag.is_server_key_only,
      multivariate_options: projectFlag.multivariate_options.map((v) => {
        const matching =
          multivariate_options &&
          multivariate_options.find(
            (m) => v.id === m.multivariate_feature_option,
          )
        return {
          ...v,
          default_percentage_allocation: matching
            ? matching.percentage_allocation
            : v.default_percentage_allocation,
        }
      }),
      name: projectFlag.name,
      tags: projectFlag.tags,
      type: projectFlag.type,
    }
  },
  getFlagsmithHasFeature(key: string) {
    return flagsmith.hasFeature(key)
  },
  getFlagsmithValue(key: string) {
    return flagsmith.getValue(key)
  },
  getIdentitiesEndpoint(_project: ProjectType) {
    const project = _project || ProjectStore.model
    if (
      Utils.getFlagsmithHasFeature('edge_identities') &&
      project &&
      project.use_edge_identities
    ) {
      return 'edge-identities'
    }
    return 'identities'
  },
  getIsEdge() {
    const model = ProjectStore.model as null | ProjectType

    if (
      Utils.getFlagsmithHasFeature('edge_identities') &&
      ProjectStore.model &&
      model?.use_edge_identities
    ) {
      return true
    }
    return false
  },
  getManageFeaturePermission(isChangeRequest: boolean) {
    if (isChangeRequest) {
      return 'CREATE_CHANGE_REQUEST'
    }
    return 'UPDATE_FEATURE_STATE'
  },
  getManageFeaturePermissionDescription(isChangeRequest: boolean) {
    if (isChangeRequest) {
      return 'Create Change Request'
    }
    return 'Update Feature State'
  },
  getManageUserPermission() {
    return 'MANAGE_IDENTITIES'
  },
  getManageUserPermissionDescription() {
    return 'Manage Identities'
  },
  getPlanName: (plan: string) => {
    if (plan && plan.includes('scale-up')) {
      return planNames.scaleUp
    }
    if (plan && plan.includes('side-project')) {
      return planNames.sideProject
    }
    if (plan && plan.includes('startup')) {
      return planNames.startup
    }
    if (plan && plan.includes('start-up')) {
      return planNames.startup
    }
    if (plan && plan.includes('enterprise')) {
      return planNames.enterprise
    }
    return planNames.free
  },
  getPlanPermission: (plan: string, permission: string) => {
    let valid = true
    const planName = Utils.getPlanName(plan)
    if (!Utils.getFlagsmithHasFeature('plan_based_access')) {
      return true
    }
    if (!plan || planName === planNames.free) {
      return false
    }
    const isSideProjectOrGreater = planName !== planNames.sideProject
    const isScaleupOrGreater =
      isSideProjectOrGreater && planName !== planNames.startup
    switch (permission) {
      case 'FLAG_OWNERS': {
        valid = isScaleupOrGreater
        break
      }
      case 'CREATE_ADDITIONAL_PROJECT': {
        valid = isSideProjectOrGreater
        break
      }
      case '2FA': {
        valid = isSideProjectOrGreater
        break
      }
      case 'RBAC': {
        valid = isSideProjectOrGreater
        break
      }
      case 'AUDIT': {
        valid = isScaleupOrGreater
        break
      }
      case 'AUTO_SEATS': {
        valid = isScaleupOrGreater
        break
      }
      case 'FORCE_2FA': {
        valid = isScaleupOrGreater
        break
      }
      case 'SCHEDULE_FLAGS': {
        valid = isSideProjectOrGreater
        break
      }
      case '4_EYES': {
        valid = isScaleupOrGreater
        break
      }
      default:
        valid = true
        break
    }
    return valid
  },

  getPlansPermission: (permission: string) => {
    if (!Utils.getFlagsmithHasFeature('plan_based_access')) {
      return true
    }
    const isOrgPermission = permission !== '2FA'
    const plans = isOrgPermission
      ? AccountStore.getActiveOrgPlan()
        ? [AccountStore.getActiveOrgPlan()]
        : null
      : AccountStore.getPlans()

    if (!plans || !plans.length) {
      return false
    }
    const found = _.find(
      plans.map((plan: string) => Utils.getPlanPermission(plan, permission)),
      (perm) => !!perm,
    )
    return !!found
  },
  getSDKEndpoint(_project: ProjectType) {
    const project = _project || ProjectStore.model

    if (
      Utils.getFlagsmithHasFeature('edge_identities') &&
      project &&
      project.use_edge_identities
    ) {
      return Project.flagsmithClientEdgeAPI
    }
    return Project.api
  },

  getShouldHideIdentityOverridesTab(_project: ProjectType) {
    const project = _project || ProjectStore.model
    if (
      Utils.getFlagsmithHasFeature('edge_identities') &&
      project &&
      project.use_edge_identities
    ) {
      return true
    }
    return false
  },

  getShouldSendIdentityToTraits(_project: ProjectType) {
    const project = _project || ProjectStore.model
    if (
      Utils.getFlagsmithHasFeature('edge_identities') &&
      project &&
      project.use_edge_identities
    ) {
      return false
    }
    return true
  },

  getShouldUpdateTraitOnDelete(_project: ProjectType) {
    const project = _project || ProjectStore.model
    if (
      Utils.getFlagsmithHasFeature('edge_identities') &&
      project &&
      project.use_edge_identities
    ) {
      return true
    }
    return false
  },

  getTraitEndpoint(environmentId: string, userId: string) {
    const model = ProjectStore.model as null | ProjectType

    if (
      Utils.getFlagsmithHasFeature('edge_identities') &&
      model?.use_edge_identities
    ) {
      return `${Project.api}environments/${environmentId}/edge-identities/${userId}/list-traits/`
    }
    return `${Project.api}environments/${environmentId}/identities/${userId}/traits/`
  },

  getTraitEndpointMethod(id?: number) {
    if (
      Utils.getFlagsmithHasFeature('edge_identities') &&
      (ProjectStore.model as ProjectType | null)?.use_edge_identities
    ) {
      return 'put'
    }
    return id ? 'put' : 'post'
  },

  getTypedValue(str: FlagsmithValue, boolToString?: boolean) {
    if (typeof str === 'undefined') {
      return ''
    }
    if (typeof str !== 'string') {
      return str
    }

    const isNum = /^\d+$/.test(str)

    if (isNum && parseInt(str) > Number.MAX_SAFE_INTEGER) {
      return `${str}`
    }

    if (str === 'true') {
      if (boolToString) return 'true'
      return true
    }
    if (str === 'false') {
      if (boolToString) return 'false'
      return false
    }

    if (isNum) {
      if (str.indexOf('.') !== -1) {
        return parseFloat(str)
      }
      return parseInt(str)
    }

    return str
  },

  getUpdateTraitEndpoint(environmentId: string, userId: string, id?: string) {
    if (
      Utils.getFlagsmithHasFeature('edge_identities') &&
      (ProjectStore.model as ProjectType | null)?.use_edge_identities
    ) {
      return `${Project.api}environments/${environmentId}/edge-identities/${userId}/update-traits/`
    }
    return `${
      Project.api
    }environments/${environmentId}/identities/${userId}/traits/${
      id ? `${id}/` : ''
    }`
  },

  getViewIdentitiesPermission() {
    return 'VIEW_IDENTITIES'
  },

  isMigrating() {
    const model = ProjectStore.model as null | ProjectType
    if (
      Utils.getFlagsmithHasFeature('edge_identities') &&
      (model?.migration_status === 'MIGRATION_IN_PROGRESS' ||
        model?.migration_status === 'MIGRATION_SCHEDULED')
    ) {
      return true
    }
    return false
  },
  loadScriptPromise(url: string) {
    return new Promise((resolve) => {
      const cb = function () {
        // @ts-ignore
        this.removeEventListener('load', cb)
        resolve(null)
      }
      const head = document.getElementsByTagName('head')[0]
      const script = document.createElement('script')
      script.type = 'text/javascript'
      script.addEventListener('load', cb)
      script.src = url
      head.appendChild(script)
    })
  },
  numberWithCommas(x: number) {
    if (typeof x !== 'number') return ''
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  },
  openChat() {
    // @ts-ignore
    if (typeof $crisp !== 'undefined') {
      // @ts-ignore
      $crisp.push(['do', 'chat:open'])
    }
    // @ts-ignore
    if (window.zE) {
      // @ts-ignore
      zE('messenger', 'open')
    }
  },

  removeElementFromArray(array: any[], index: number) {
    return array.slice(0, index).concat(array.slice(index + 1))
  },

  renderWithPermission(permission: boolean, name: string, el: ReactNode) {
    return permission ? (
      el
    ) : (
      <Tooltip title={<div>{el}</div>} place='right' html>
        {name}
      </Tooltip>
    )
  },
  validateRule(rule: SegmentCondition) {
    if (!rule) return false

    if (rule.delete) {
      return true
    }

    const operators = Utils.getFlagsmithValue('segment_operators')
      ? JSON.parse(Utils.getFlagsmithValue('segment_operators'))
      : []
    const operatorObj = Utils.findOperator(rule.operator, rule.value, operators)

    if (
      operatorObj &&
      operatorObj.value &&
      operatorObj.value.toLowerCase().includes('semver')
    ) {
      return !!semver.valid(`${rule.value.split(':')[0]}`)
    }

    switch (rule.operator) {
      case 'PERCENTAGE_SPLIT': {
        const value = parseFloat(rule.value)
        return !isNaN(value) && value >= 0 && value <= 100
      }
      case 'REGEX': {
        try {
          if (!rule.value) {
            throw new Error('')
          }
          new RegExp(`${rule.value}`)
          return true
        } catch (e) {
          return false
        }
      }
      case 'MODULO': {
        const valueSplit = rule.value.split('|')
        if (valueSplit.length === 2) {
          const [divisor, remainder] = [
            parseFloat(valueSplit[0]),
            parseFloat(valueSplit[1]),
          ]
          return (
            !isNaN(divisor) &&
            divisor > 0 &&
            !isNaN(remainder) &&
            remainder >= 0
          )
        }
        return false
      }
      default:
        return (
          (operatorObj && operatorObj.hideValue) ||
          (rule.value !== '' && rule.value !== undefined && rule.value !== null)
        )
    }
  },
  valueToFeatureState(value: FlagsmithValue) {
    const val = Utils.getTypedValue(value)

    if (typeof val === 'boolean') {
      return {
        boolean_value: val,
        integer_value: null,
        string_value: null,
        type: 'bool',
      }
    }

    if (typeof val === 'number') {
      return {
        boolean_value: null,
        integer_value: val,
        string_value: null,
        type: 'int',
      }
    }

    return {
      boolean_value: null,
      integer_value: null,
      string_value: value === null ? null : val || '',
      type: 'unicode',
    }
  },

  valueToTrait(value: FlagsmithValue) {
    const val = Utils.getTypedValue(value)

    if (typeof val === 'boolean') {
      return {
        boolean_value: val,
        integer_value: null,
        string_value: null,
        value_type: 'bool',
      }
    }

    if (typeof val === 'number') {
      return {
        boolean_value: null,
        integer_value: val,
        string_value: null,
        value_type: 'int',
      }
    }

    return {
      boolean_value: null,
      integer_value: null,
      string_value: value === null ? null : val || '',
      value_type: 'unicode',
    }
  },
})

export default Utils
