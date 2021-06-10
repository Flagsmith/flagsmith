const AppActions = Object.assign({}, require('./base/_app-actions'), {
    getOrganisation(organisationId) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_ORGANISATION,
            id: organisationId,
        });
    },
    oauthLogin(oauthType, data) {
        Dispatcher.handleViewAction({
            actionType: Actions.OAUTH,
            oauthType,
            data,
        });
    },
    getFeatures(projectId, environmentId, force) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_FLAGS,
            projectId,
            environmentId,
            force
        });
    },
    createProject(name) {
        Dispatcher.handleViewAction({
            actionType: Actions.CREATE_PROJECT,
            name,
        });
    },

    getGroupsPage(orgId, page) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_GROUPS_PAGE,
            orgId,
            page,
        });
    },

    getTags(projectId) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_TAGS,
            projectId,
        });
    },

    updateTag(projectId, data, onComplete) {
        Dispatcher.handleViewAction({
            actionType: Actions.UPDATE_TAG,
            projectId,
            data,
            onComplete,
        });
    },

    createTag(projectId, data, onComplete) {
        Dispatcher.handleViewAction({
            actionType: Actions.CREATE_TAG,
            projectId,
            data,
            onComplete,
        });
    },

    deleteTag(projectId, data, onComplete) {
        Dispatcher.handleViewAction({
            actionType: Actions.DELETE_TAG,
            projectId,
            data,
            onComplete,
        });
    },

    getGroups(orgId) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_GROUPS,
            orgId,
        });
    },
    createGroup(orgId, data) {
        Dispatcher.handleViewAction({
            actionType: Actions.CREATE_GROUP,
            data,
            orgId,
        });
    },
    deleteGroup(orgId, data) {
        Dispatcher.handleViewAction({
            actionType: Actions.DELETE_GROUP,
            data,
            orgId,
        });
    },
    updateGroup(orgId, data) {
        Dispatcher.handleViewAction({
            actionType: Actions.UPDATE_GROUP,
            data,
            orgId,
        });
    },
    getPermissions(id, level) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_PERMISSIONS,
            id,
            level,
        });
    },
    getAvailablePermissions() {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_AVAILABLE_PERMISSIONS,
        });
    },
    getProject(projectId) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_PROJECT,
            projectId,
        });
    },
    getConfig(projectId) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_CONFIG,
            projectId,
        });
    },
    resetPassword(data) {
        Dispatcher.handleViewAction({
            actionType: Actions.RESET_PASSWORD,
            ...data,
        });
    },
    createEnv(name, projectId) {
        Dispatcher.handleViewAction({
            actionType: Actions.CREATE_ENV,
            name,
            projectId,
        });
    },
    editEnv(env) {
        Dispatcher.handleViewAction({
            actionType: Actions.EDIT_ENVIRONMENT,
            env,
        });
    },
    deleteEnv(env) {
        Dispatcher.handleViewAction({
            actionType: Actions.DELETE_ENVIRONMENT,
            env,
        });
    },
    refreshOrganisation() {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_ORGANISATION,
            force: true,
        });
    },
    getFlagInfluxData(projectId, environmentId, flag, period) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_FLAG_INFLUX_DATA,
            projectId,
            environmentId,
            flag,
            period,
        });
    },
    createFlag(projectId, environmentId, flag, segmentOverrides) {
        Dispatcher.handleViewAction({
            actionType: Actions.CREATE_FLAG,
            projectId,
            environmentId,
            flag,
            segmentOverrides,
        });
    },
    editEnvironmentFlag(projectId, environmentId, flag, projectFlag, environmentFlag, segmentOverrides) {
        Dispatcher.handleViewAction({
            actionType: Actions.EDIT_ENVIRONMENT_FLAG,
            projectId,
            environmentId,
            flag,
            projectFlag,
            environmentFlag,
            segmentOverrides,
        });
    },

    editFlag(projectId, flag,onComplete) {
        Dispatcher.handleViewAction({
            actionType: Actions.EDIT_FLAG,
            projectId,
            flag,
            onComplete
        });
    },
    editProject(id, project) {
        Dispatcher.handleViewAction({
            actionType: Actions.EDIT_PROJECT,
            id,
            project,
        });
    },
    removeUserFlag({ environmentId, identity, identityFlag }) {
        Dispatcher.handleViewAction({
            actionType: Actions.REMOVE_USER_FLAG,
            environmentId,
            identity,
            identityFlag,
        });
    },
    acceptInvite(id) {
        Dispatcher.handleViewAction({
            actionType: Actions.ACCEPT_INVITE,
            id,
        });
    },
    deleteProject(id) {
        Dispatcher.handleViewAction({
            actionType: Actions.DELETE_PROJECT,
            id,
        });
    },
    saveEnv(name) {
        Dispatcher.handleViewAction({
            actionType: Actions.EDIT_ENVIRONMENT,
            name,
        });
    },
    toggleFlag(index, environments, comment) {
        Dispatcher.handleViewAction({
            actionType: Actions.TOGGLE_FLAG,
            index,
            environments,
            comment,
        });
    },
    editUserFlag(params) {
        Dispatcher.handleViewAction({
            actionType: Actions.EDIT_USER_FLAG,
            ...params,
        });
    },
    editTrait(params) {
        Dispatcher.handleViewAction({
            actionType: Actions.EDIT_TRAIT,
            ...params,
        });
    },
    toggleUserFlag(params) {
        Dispatcher.handleViewAction({
            actionType: Actions.TOGGLE_USER_FLAG,
            ...params,
        });
    },
    changeUserFlag(identity) {
        Dispatcher.handleViewAction({
            actionType: Actions.CHANGE_USER_FLAG,
            identity,
        });
    },
    selectOrganisation(id) {
        Dispatcher.handleViewAction({
            actionType: Actions.SELECT_ORGANISATION,
            id,
        });
    },
    enableTwoFactor() {
        Dispatcher.handleViewAction({
            actionType: Actions.ENABLE_TWO_FACTOR,
        });
    },
    disableTwoFactor() {
        Dispatcher.handleViewAction({
            actionType: Actions.DISABLE_TWO_FACTOR,
        });
    },
    confirmTwoFactor(pin, onError) {
        Dispatcher.handleViewAction({
            actionType: Actions.CONFIRM_TWO_FACTOR,
            pin,
            onError,
        });
    },
    twoFactorLogin(pin, onError) {
        Dispatcher.handleViewAction({
            actionType: Actions.TWO_FACTOR_LOGIN,
            pin,
            onError,
        });
    },
    getIdentities(envId, pageSize) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_IDENTITIES,
            envId,
            pageSize,
        });
    },
    getIdentitiesPage(envId, page) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_IDENTITIES_PAGE,
            envId,
            page,
        });
    },
    getIdentity(envId, id) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_IDENTITY,
            envId,
            id,
        });
    },
    getIdentitySegments(projectId, id) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_IDENTITY_SEGMENTS,
            projectId,
            id,
        });
    },
    getIdentitySegmentsPage(page) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_IDENTITY_SEGMENTS_PAGE,
            page,
        });
    },
    saveIdentity(id, identity) {
        Dispatcher.handleViewAction({
            actionType: Actions.SAVE_IDENTITY,
            id,
            identity,
        });
    },
    createOrganisation(name) {
        Dispatcher.handleViewAction({
            actionType: Actions.CREATE_ORGANISATION,
            name,
        });
    },
    editOrganisation(org) {
        Dispatcher.handleViewAction({
            actionType: Actions.EDIT_ORGANISATION,
            org,
        });
    },
    removeFlag(projectId, flag) {
        Dispatcher.handleViewAction({
            actionType: Actions.REMOVE_FLAG,
            projectId,
            flag,
        });
    },
    deleteOrganisation() {
        Dispatcher.handleViewAction({
            actionType: Actions.DELETE_ORGANISATION,
        });
    },
    // Invites todo: organise actions
    inviteUsers(invites) {
        Dispatcher.handleViewAction({
            actionType: Actions.INVITE_USERS,
            invites,
        });
    },
    deleteInvite(id) {
        Dispatcher.handleViewAction({
            actionType: Actions.DELETE_INVITE,
            id,
        });
    },
    deleteUser(id) {
        Dispatcher.handleViewAction({
            actionType: Actions.DELETE_USER,
            id,
        });
    },
    resendInvite(id) {
        Dispatcher.handleViewAction({
            actionType: Actions.RESEND_INVITE,
            id,
        });
    },
    // Segments
    selectEnvironment(data) {
        Dispatcher.handleViewAction({
            actionType: Actions.SELECT_ENVIRONMENT,
            data,
        });
    },
    getSegments(projectId, environmentId) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_SEGMENTS,
            projectId,
            environmentId,
        });
    },
    createSegment(projectId, segment) {
        Dispatcher.handleViewAction({
            actionType: Actions.CREATE_SEGMENT,
            projectId,
            data: segment,
        });
    },
    editSegment(projectId, segment) {
        Dispatcher.handleViewAction({
            actionType: Actions.EDIT_SEGMENT,
            projectId,
            data: segment,
        });
    },
    removeSegment(projectId, id) {
        Dispatcher.handleViewAction({
            actionType: Actions.REMOVE_SEGMENT,
            projectId,
            id,
        });
    },
    searchIdentities(envId, search, pageSize) {
        Dispatcher.handleViewAction({
            actionType: Actions.SEARCH_IDENTITIES,
            envId,
            search,
            pageSize,
        });
    },
    getAuditLog() {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_AUDIT_LOG,
        });
    },
    getAuditLogPage(page) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_AUDIT_LOG_PAGE,
            page,
        });
    },
    searchAuditLog(search) {
        Dispatcher.handleViewAction({
            actionType: Actions.SEARCH_AUDIT_LOG,
            search,
        });
    },
    deleteIdentity(envId, id) {
        Dispatcher.handleViewAction({
            actionType: Actions.DELETE_IDENTITY,
            envId,
            id,
        });
    },
    deleteIdentityTrait(envId, identity, id) {
        Dispatcher.handleViewAction({
            actionType: Actions.DELETE_IDENTITY_TRAIT,
            envId,
            identity,
            id,
        });
    },
    updateUserRole(id, role) {
        Dispatcher.handleViewAction({
            actionType: Actions.UPDATE_USER_ROLE,
            id,
            role,
        });
    },
    updateSubscription(hostedPageId) {
        Dispatcher.handleViewAction({
            actionType: Actions.UPDATE_SUBSCRIPTION,
            hostedPageId,
        });
    },
    getInfluxData(organisationId) {
        Dispatcher.handleViewAction({
            actionType: Actions.GET_INFLUX_DATA,
            id: organisationId,
        });
    },
});

module.exports = AppActions;
window.AppActions = AppActions;
