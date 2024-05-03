const Dispatcher = require('../dispatcher/dispatcher')

const AppActions = Object.assign({}, require('./base/_app-actions'), {
  acceptInvite(id) {
    Dispatcher.handleViewAction({
      actionType: Actions.ACCEPT_INVITE,
      id,
    })
  },
  actionChangeRequest(id, action, cb) {
    Dispatcher.handleViewAction({
      action,
      actionType: Actions.ACTION_CHANGE_REQUEST,
      cb,
      id,
    })
  },
  changeUserFlag(identity) {
    Dispatcher.handleViewAction({
      actionType: Actions.CHANGE_USER_FLAG,
      identity,
    })
  },
  confirmTwoFactor(pin, onError, isLoginPage) {
    Dispatcher.handleViewAction({
      actionType: Actions.CONFIRM_TWO_FACTOR,
      isLoginPage,
      onError,
      pin,
    })
  },
  createEnv(name, projectId, cloneId, description) {
    Dispatcher.handleViewAction({
      actionType: Actions.CREATE_ENV,
      cloneId,
      description,
      name,
      projectId,
    })
  },
  createFlag(projectId, environmentId, flag, segmentOverrides) {
    Dispatcher.handleViewAction({
      actionType: Actions.CREATE_FLAG,
      environmentId,
      flag,
      projectId,
      segmentOverrides,
    })
  },
  createOrganisation(name) {
    Dispatcher.handleViewAction({
      actionType: Actions.CREATE_ORGANISATION,
      name,
    })
  },
  createProject(name) {
    Dispatcher.handleViewAction({
      actionType: Actions.CREATE_PROJECT,
      name,
    })
  },

  deleteChangeRequest(id, cb) {
    Dispatcher.handleViewAction({
      actionType: Actions.DELETE_CHANGE_REQUEST,
      cb,
      id,
    })
  },
  deleteEnv(env) {
    Dispatcher.handleViewAction({
      actionType: Actions.DELETE_ENVIRONMENT,
      env,
    })
  },
  deleteIdentityTrait(envId, identity, id) {
    Dispatcher.handleViewAction({
      actionType: Actions.DELETE_IDENTITY_TRAIT,
      envId,
      id,
      identity,
    })
  },
  deleteInvite(id) {
    Dispatcher.handleViewAction({
      actionType: Actions.DELETE_INVITE,
      id,
    })
  },
  deleteOrganisation() {
    Dispatcher.handleViewAction({
      actionType: Actions.DELETE_ORGANISATION,
    })
  },
  deleteProject(id) {
    Dispatcher.handleViewAction({
      actionType: Actions.DELETE_PROJECT,
      id,
    })
  },
  deleteUser(id) {
    Dispatcher.handleViewAction({
      actionType: Actions.DELETE_USER,
      id,
    })
  },
  disableTwoFactor() {
    Dispatcher.handleViewAction({
      actionType: Actions.DISABLE_TWO_FACTOR,
    })
  },
  editEnv(env) {
    Dispatcher.handleViewAction({
      actionType: Actions.EDIT_ENVIRONMENT,
      env,
    })
  },
  editEnvironmentFlag(
    projectId,
    environmentId,
    flag,
    projectFlag,
    environmentFlag,
    segmentOverrides,
    mode,
    onComplete,
  ) {
    Dispatcher.handleViewAction({
      actionType: Actions.EDIT_ENVIRONMENT_FLAG,
      environmentFlag,
      environmentId,
      flag,
      mode,
      onComplete,
      projectFlag,
      projectId,
      segmentOverrides,
    })
  },
  editEnvironmentFlagChangeRequest(
    projectId,
    environmentId,
    flag,
    projectFlag,
    environmentFlag,
    segmentOverrides,
    changeRequest,
    commit,
  ) {
    Dispatcher.handleViewAction({
      actionType: Actions.EDIT_ENVIRONMENT_FLAG_CHANGE_REQUEST,
      changeRequest,
      commit,
      environmentFlag,
      environmentId,
      flag,
      projectFlag,
      projectId,
      segmentOverrides,
    })
  },
  editFeature(projectId, flag, onComplete) {
    Dispatcher.handleViewAction({
      actionType: Actions.EDIT_FEATURE,
      flag,
      onComplete,
      projectId,
    })
  },

  editFeatureMv(projectId, flag, onComplete) {
    Dispatcher.handleViewAction({
      actionType: Actions.EDIT_FEATURE_MV,
      flag,
      onComplete,
      projectId,
    })
  },

  editOrganisation(org) {
    Dispatcher.handleViewAction({
      actionType: Actions.EDIT_ORGANISATION,
      org,
    })
  },

  editProject(id, project) {
    Dispatcher.handleViewAction({
      actionType: Actions.EDIT_PROJECT,
      id,
      project,
    })
  },
  editTrait(params) {
    Dispatcher.handleViewAction({
      actionType: Actions.EDIT_TRAIT,
      ...params,
    })
  },
  editUserFlag(params) {
    Dispatcher.handleViewAction({
      actionType: Actions.EDIT_USER_FLAG,
      ...params,
    })
  },
  enableTwoFactor() {
    Dispatcher.handleViewAction({
      actionType: Actions.ENABLE_TWO_FACTOR,
    })
  },
  getChangeRequest(id, projectId, environmentId) {
    Dispatcher.handleViewAction({
      actionType: Actions.GET_CHANGE_REQUEST,
      environmentId,
      id,
      projectId,
    })
  },
  getChangeRequests(environment, data, page) {
    Dispatcher.handleViewAction({
      actionType: Actions.GET_CHANGE_REQUESTS,
      committed: data.committed,
      environment,
      live_from_after: data.live_from_after,
      page,
    })
  },
  getFeatureUsage(projectId, environmentId, flag, period) {
    Dispatcher.handleViewAction({
      actionType: Actions.GET_FEATURE_USAGE,
      environmentId,
      flag,
      period,
      projectId,
    })
  },
  getFeatures(
    projectId,
    environmentId,
    force,
    search,
    sort,
    page,
    filter,
    pageSize,
  ) {
    Dispatcher.handleViewAction({
      actionType: Actions.GET_FLAGS,
      environmentId,
      filter,
      force,
      page,
      pageSize,
      projectId,
      search,
      sort,
    })
  },
  getIdentity(envId, id) {
    Dispatcher.handleViewAction({
      actionType: Actions.GET_IDENTITY,
      envId,
      id,
    })
  },
  getIdentitySegments(projectId, id) {
    Dispatcher.handleViewAction({
      actionType: Actions.GET_IDENTITY_SEGMENTS,
      id,
      projectId,
    })
  },
  getOrganisation(organisationId) {
    Dispatcher.handleViewAction({
      actionType: Actions.GET_ORGANISATION,
      id: organisationId,
    })
  },
  getProject(projectId) {
    Dispatcher.handleViewAction({
      actionType: Actions.GET_PROJECT,
      projectId,
    })
  },
  invalidateInviteLink(link) {
    Dispatcher.handleViewAction({
      actionType: Actions.INVALIDATE_INVITE_LINK,
      link,
    })
  },
  inviteUsers(invites) {
    Dispatcher.handleViewAction({
      actionType: Actions.INVITE_USERS,
      invites,
    })
  },
  migrateProject(projectId) {
    Dispatcher.handleViewAction({
      actionType: Actions.MIGRATE_PROJECT,
      projectId,
    })
  },
  oauthLogin(oauthType, data) {
    Dispatcher.handleViewAction({
      actionType: Actions.OAUTH,
      data,
      oauthType,
    })
  },
  refreshFeatures(projectId, environmentId) {
    Dispatcher.handleViewAction({
      actionType: Actions.REFRESH_FEATURES,
      environmentId,
      projectId,
    })
  },
  refreshOrganisation() {
    Dispatcher.handleViewAction({
      actionType: Actions.GET_ORGANISATION,
      force: true,
    })
  },
  removeFlag(projectId, flag) {
    Dispatcher.handleViewAction({
      actionType: Actions.REMOVE_FLAG,
      flag,
      projectId,
    })
  },
  removeUserFlag({ cb, environmentId, identity, identityFlag }) {
    Dispatcher.handleViewAction({
      actionType: Actions.REMOVE_USER_FLAG,
      cb,
      environmentId,
      identity,
      identityFlag,
    })
  },
  resendInvite(id) {
    Dispatcher.handleViewAction({
      actionType: Actions.RESEND_INVITE,
      id,
    })
  },
  resetPassword(data) {
    Dispatcher.handleViewAction({
      actionType: Actions.RESET_PASSWORD,
      ...data,
    })
  },
  saveEnv(name) {
    Dispatcher.handleViewAction({
      actionType: Actions.EDIT_ENVIRONMENT,
      name,
    })
  },
  searchFeatures(
    projectId,
    environmentId,
    force,
    search,
    sort,
    filter,
    pageSize,
  ) {
    Dispatcher.handleViewAction({
      actionType: Actions.SEARCH_FLAGS,
      environmentId,
      filter,
      force,
      pageSize,
      projectId,
      search,
      sort,
    })
  },
  selectOrganisation(id) {
    Dispatcher.handleViewAction({
      actionType: Actions.SELECT_ORGANISATION,
      id,
    })
  },
  toggleFlag(index, environments, comment, environmentFlags, projectFlags) {
    Dispatcher.handleViewAction({
      actionType: Actions.TOGGLE_FLAG,
      comment,
      environmentFlags,
      environments,
      index,
      projectFlags,
    })
  },
  toggleUserFlag(params) {
    Dispatcher.handleViewAction({
      actionType: Actions.TOGGLE_USER_FLAG,
      ...params,
    })
  },
  twoFactorLogin(pin, onError) {
    Dispatcher.handleViewAction({
      actionType: Actions.TWO_FACTOR_LOGIN,
      onError,
      pin,
    })
  },
  updateChangeRequest(changeRequest) {
    Dispatcher.handleViewAction({
      actionType: Actions.UPDATE_CHANGE_REQUEST,
      changeRequest,
    })
  },
  updateSubscription(hostedPageId) {
    Dispatcher.handleViewAction({
      actionType: Actions.UPDATE_SUBSCRIPTION,
      hostedPageId,
    })
  },
  updateUserRole(id, role) {
    Dispatcher.handleViewAction({
      actionType: Actions.UPDATE_USER_ROLE,
      id,
      role,
    })
  },
})

module.exports = AppActions
window.AppActions = AppActions
