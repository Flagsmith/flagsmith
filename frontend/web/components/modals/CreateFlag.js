import React, { Component } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip as RechartsTooltip, XAxis, YAxis } from 'recharts';
import Tabs from '../base/forms/Tabs';
import TabItem from '../base/forms/TabItem';
import withSegmentOverrides from '../../../common/providers/withSegmentOverrides';
import data from '../../../common/data/base/_data';
import ProjectStore from '../../../common/stores/project-store';
import _data from '../../../common/data/base/_data';
import SegmentOverrides from '../SegmentOverrides';
import AddEditTags from '../AddEditTags';
import Constants from '../../../common/constants';
import FlagOwners from '../FlagOwners';
import FeatureListStore from '../../../common/stores/feature-list-store';
import ChangeRequestModal from './ChangeRequestModal';
import Feature from '../Feature';
import { ButtonOutline } from '../base/forms/Button';
import ChangeRequestStore from '../../../common/stores/change-requests-store'
const FEATURE_ID_MAXLENGTH = Constants.forms.maxLength.FEATURE_ID;

const CreateFlag = class extends Component {
    static displayName = 'CreateFlag'

    constructor(props, context) {
        super(props, context);
        const { name, feature_state_value, description, is_archived, tags, enabled, hide_from_client, multivariate_options } = this.props.isEdit ? Utils.getFlagValue(this.props.projectFlag, this.props.environmentFlag, this.props.identityFlag)
            : {
                multivariate_options: [],
            };
        const { allowEditDescription } = this.props;
        if (this.props.projectFlag) {
            this.userOverridesPage(1);
        }
        this.state = {
            default_enabled: enabled,
            hide_from_client,
            name,
            tags: tags || [],
            initial_value: typeof feature_state_value === 'undefined' ? undefined : Utils.getTypedValue(feature_state_value),
            description,
            multivariate_options: _.cloneDeep(multivariate_options),
            identityVariations: this.props.identityFlag && this.props.identityFlag.multivariate_feature_state_values ? _.cloneDeep(this.props.identityFlag.multivariate_feature_state_values) : [],
            selectedIdentity: null,
            allowEditDescription,
            enabledIndentity: false,
            enabledSegment: false,
            is_archived,
            period: '24h',
        };
    }


    close() {
        closeModal();
    }


    componentDidUpdate(prevProps, prevState, snapshot) {
        if (!this.props.identity && this.props.environmentVariations !== prevProps.environmentVariations) {
            if (this.props.environmentVariations && this.props.environmentVariations.length) {
                this.setState({
                    multivariate_options: this.state.multivariate_options && this.state.multivariate_options.map((v) => {
                        const matchingVariation = (this.props.multivariate_options || this.props.environmentVariations).find(e => e.multivariate_feature_option === v.id);
                        return {
                            ...v,
                            default_percentage_allocation: matchingVariation && matchingVariation.percentage_allocation || 0,
                        };
                    }),
                });
            }
        }
    }


    componentDidMount = () => {
        if (!this.props.isEdit && !E2E) {
            this.focusTimeout = setTimeout(() => {
                this.input.focus();
                this.focusTimeout = null;
            }, 500);
        }
        AppActions.getIdentities(this.props.environmentId, 3);
        if (!projectOverrides.disableInflux && this.props.projectFlag && this.props.environmentFlag) {
            this.getInfluxData();
        }
    };

    componentWillUnmount() {
        if (this.focusTimeout) {
            clearTimeout(this.focusTimeout);
        }
    }

    userOverridesPage = (page) => {
        data.get(`${Project.api}environments/${this.props.environmentId}/featurestates/?anyIdentity=1&feature=${this.props.projectFlag.id}&page=${page}`)
            .then((userOverrides) => {
                this.setState({
                    userOverrides: userOverrides.results,
                    userOverridesPaging: {
                        next: userOverrides.next,
                        count: userOverrides.count,
                        currentPage: page,
                    },
                });
            });
    }

    getInfluxData = () => {
        if (this.props.hasFeature('flag_analytics') && this.props.environmentFlag) {
            AppActions.getFlagInfluxData(this.props.projectId, this.props.environmentFlag.environment, this.props.projectFlag.id, this.state.period);
        }
    }

    getDisplayPeriod = () => {
        const { period } = this.state;
        if (period == '24h') {
            return '30d';
        }
        return '24h';
    }

    changePeriod = () => {
        const changePeriod = this.getDisplayPeriod();
        this.state = {
            ...this.state,
            period: changePeriod,
        };
        this.getInfluxData();
    }

    save = (func, isSaving) => {
        const { projectFlag, segmentOverrides, environmentFlag, identity, identityFlag, environmentId } = this.props;
        const { name, initial_value, description, is_archived, default_enabled, hide_from_client } = this.state;
        const hasMultivariate = this.props.environmentFlag && this.props.environmentFlag.multivariate_feature_state_values && this.props.environmentFlag.multivariate_feature_state_values.length;
        if (identity) {
            !isSaving && name && func({
                identity,
                projectFlag,
                environmentFlag,
                identityFlag: Object.assign({}, identityFlag || {}, {
                    multivariate_options: this.state.identityVariations,
                    feature_state_value: hasMultivariate ? this.props.environmentFlag.feature_state_value : initial_value,
                    enabled: default_enabled,
                }),
                environmentId,
            });
        } else {
            FeatureListStore.isSaving = true;
            FeatureListStore.trigger('change');
            !isSaving && name && func(this.props.projectId, this.props.environmentId, {
                name,
                initial_value,
                default_enabled,
                tags: this.state.tags,
                hide_from_client,
                description,
                is_archived,
                multivariate_options: this.state.multivariate_options,
            }, projectFlag, environmentFlag, segmentOverrides);
        }
    }

    changeSegment = (items) => {
        const { enabledSegment } = this.state;
        items.forEach((item) => {
            item.enabled = enabledSegment;
        });
        this.props.updateSegments(items);
        this.setState({ enabledSegment: !enabledSegment });
    }

    changeIdentity = (items) => {
        const { environmentId } = this.props;
        const { enabledIndentity } = this.state;

        Promise.all(items.map(item => new Promise((resolve) => {
            AppActions.changeUserFlag({
                identityFlag: item.id,
                identity: item.identity.id,
                environmentId,
                onSuccess: resolve,
                payload: {
                    id: item.identity.id,
                    enabled: enabledIndentity,
                    value: item.identity.identifier,
                },
            });
        }))).then(() => {
            this.userOverridesPage(1);
        });

        this.setState({ enabledIndentity: !enabledIndentity });
    }

    toggleUserFlag = ({ id, feature_state_value, enabled, identity }) => {
        const { environmentId } = this.props;

        AppActions.changeUserFlag({
            identityFlag: id,
            identity: identity.id,
            environmentId,
            onSuccess: () => {
                this.userOverridesPage(1);
            },
            payload: {
                id: identity.id,
                enabled: !enabled,
                value: identity.identifier,
            },
        });
    }

    drawChart = (data) => {
        const { name } = this.state;
        if (data && data.events_list) { // protect against influx setup incorrectly
            return (
                <ResponsiveContainer height={400} width="100%">
                    <BarChart data={data.events_list}>
                        <CartesianGrid strokeDasharray="3 5"/>
                        <XAxis allowDataOverflow={false} dataKey="datetime"/>
                        <YAxis allowDataOverflow={false}/>
                        <RechartsTooltip/>
                        <Bar dataKey={name} stackId="a" fill="#6633ff" />
                    </BarChart>
                </ResponsiveContainer>
            );
        }
        return null;
    }

    addItem = () => {
        const { projectFlag, environmentFlag, environmentId, identity } = this.props;
        this.setState({ isLoading: true });
        const selectedIdentity = this.state.selectedIdentity.value;
        const identities = identity ? identity.identifier : [];

        if (!_.find(identities, v => v.identifier === selectedIdentity)) {
            _data.post(`${Project.api}environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${selectedIdentity}/featurestates/`, {
                feature: projectFlag.id,
                enabled: !environmentFlag.enabled,
                value: environmentFlag.value,
            }).then((res) => {
                this.setState({
                    isLoading: false,
                    selectedIdentity: null,
                });
                this.userOverridesPage(1);
            })
                .catch((e) => {
                    this.setState({ error, isLoading: false });
                });
        } else {
            this.setState({
                isLoading: false,
                selectedIdentity: null,
            });
        }
    }

    identityOptions = (identities, value, isLoading) => {
        if (!value) {
            return [];
        }
        return _.filter(
            identities, identity => !value || !_.find(value, v => v.identity.identifier === identity.identifier),
        ).map(({ identifier: label, id: value }) => ({ value, label })).slice(0, 10);
    }

    onSearchIdentityChange = (e) => {
        AppActions.searchIdentities(this.props.environmentId, Utils.safeParseEventValue(e), 3);
    }

    addVariation = () => {
        this.setState({
            multivariate_options: this.state.multivariate_options.concat([
                {
                    ...Utils.valueToFeatureState(''),
                    default_percentage_allocation: 0,
                },
            ]),
        });
    }

    removeVariation = (i) => {
        if (this.state.multivariate_options[i].id) {
            const idToRemove = this.state.multivariate_options[i].id;
            if (idToRemove) {
                this.props.removeMultiVariateOption(idToRemove);
            }
            this.state.multivariate_options.splice(i, 1);
            this.forceUpdate();
        } else {
            this.state.multivariate_options.splice(i, 1);
            this.forceUpdate();
        }
    }

    updateVariation = (i, e, environmentVariations) => {
        this.props.onEnvironmentVariationsChange(environmentVariations);
        this.state.multivariate_options[i] = e;
        this.forceUpdate();
    }


    render() {
        const {
            name,
            initial_value,
            hide_from_client,
            default_enabled,
            multivariate_options,
            description,
            is_archived,
            enabledSegment,
            enabledIndentity,
        } = this.state;
        const { isEdit, hasFeature, projectFlag, identity, identityName } = this.props;
        const Provider = identity ? IdentityProvider : FeatureListProvider;
        const environmentVariations = this.props.environmentVariations;
        const environment = ProjectStore.getEnvironment(this.props.environmentId);
        const is4Eyes = !!environment && !!environment.minimum_change_request_approvals && flagsmith.hasFeature('4eyes'); // todo: base on environment settings too
        const canSchedule = Utils.getPlansPermission('4_EYES');
        const is4EyesSegmentOverrides = is4Eyes && flagsmith.hasFeature('4eyes_segment_overrides'); //
        const controlValue = Utils.calculateControl(multivariate_options, environmentVariations);
        const invalid = !!multivariate_options && multivariate_options.length && controlValue < 0;
        const existingChangeRequest = this.props.changeRequest;
        const Settings = projectAdmin => (
            <>
                {!identity && this.state.tags && (
                    <FormGroup className="mb-4 mr-3 ml-3" >
                        <InputGroup
                          title={identity ? 'Tags' : 'Tags (optional)'}
                          tooltip={Constants.strings.TAGS_DESCRIPTION}
                          component={(
                              <AddEditTags
                                readOnly={!!identity || !projectAdmin} projectId={this.props.projectId} value={this.state.tags}
                                onChange={tags => this.setState({ tags })}
                              />
                            )}
                        />
                    </FormGroup>
                )}
                {!identity && projectFlag && (
                    <Permission level="project" permission="ADMIN" id={this.props.projectId}>
                        {({ permission: projectAdmin }) => projectAdmin && (
                            <FormGroup className="mb-4 mr-3 ml-3" >
                                <FlagOwners projectId={this.props.projectId} id={projectFlag.id}/>
                            </FormGroup>

                        )}
                    </Permission>
                )}
                <FormGroup className="mb-4 mr-3 ml-3" >
                    <InputGroup
                      value={description}
                      data-test="featureDesc"
                      inputProps={{
                          className: 'full-width',
                          readOnly: !!identity || (!projectAdmin && isEdit),
                          name: 'featureDesc',
                      }}
                      onChange={e => this.setState({ description: Utils.safeParseEventValue(e) })}
                      isValid={name && name.length}
                      ds
                      type="text" title={identity ? 'Description' : 'Description (optional)'}
                      placeholder="e.g. 'This determines what size the header is' "
                    />
                </FormGroup>
                {!identity && isEdit && (
                    <FormGroup className="mb-4 mr-3 ml-3" >
                        <InputGroup
                          value={description}
                          component={(
                              <Switch disabled={!projectAdmin} checked={this.state.is_archived} onChange={is_archived => this.setState({ is_archived })}/>
                          )}
                          onChange={e => this.setState({ description: Utils.safeParseEventValue(e) })}
                          isValid={name && name.length}
                          type="text"
                          title="Archived"
                          tooltip="Archiving a flag allows you to filter out flags from the Flagsmith dashboard that are no longer relevant.<br/>An archived flag will still return as normal in all SDK endpoints."
                          placeholder="e.g. 'This determines what size the header is' "
                        />
                    </FormGroup>
                )}


                {!identity && hasFeature('hide_flag') && (
                    <FormGroup className="mb-4 mr-3 ml-3">
                        <Tooltip
                          title={<label className="cols-sm-2 control-label">Hide from SDKs <span className="icon ion-ios-information-circle"/></label>}
                          place="right"
                        >
                            {Constants.strings.HIDE_FROM_SDKS_DESCRIPTION}
                        </Tooltip>
                        <div>
                            <Switch
                              data-test="toggle-feature-button"
                              defaultChecked={hide_from_client}
                              checked={hide_from_client}
                              onChange={hide_from_client => this.setState({ hide_from_client })}
                            />
                        </div>
                    </FormGroup>
                )}
            </>
        );
        const Value = projectAdmin => (
            <>
                {!isEdit && (
                    <FormGroup className="mb-4 mr-3 ml-3">
                        <InputGroup
                          ref={e => this.input = e}
                          data-test="featureID"
                          inputProps={{
                              readOnly: isEdit,
                              className: 'full-width',
                              name: 'featureID',
                              maxLength: FEATURE_ID_MAXLENGTH,
                          }}
                          value={name}
                          onChange={e => this.setState({ name: Format.enumeration.set(Utils.safeParseEventValue(e)).toLowerCase() })}
                          isValid={name && name.length}
                          type="text" title={isEdit ? 'ID' : 'ID*'}
                          placeholder="E.g. header_size"
                        />
                    </FormGroup>
                )}

                {identity && description && (
                    <FormGroup className="mb-4 mr-3 ml-3" >
                        <InputGroup
                          value={description}
                          data-test="featureDesc"
                          inputProps={{
                              className: 'full-width',
                              readOnly: !!identity,
                              name: 'featureDesc',
                          }}
                          onChange={e => this.setState({ description: Utils.safeParseEventValue(e) })}
                          isValid={name && name.length}
                          type="text" title={identity ? 'Description' : 'Description (optional)'}
                          placeholder="No description"
                        />
                    </FormGroup>
                )}
                <Feature
                  hide_from_client={hide_from_client}
                  multivariate_options={multivariate_options}
                  environmentVariations={environmentVariations}
                  isEdit={isEdit}
                  identity={identity}
                  removeVariation={this.removeVariation}
                  updateVariation={this.updateVariation}
                  addVariation={this.addVariation}
                  checked={default_enabled}
                  value={initial_value}
                  identityVariations={this.state.identityVariations}
                  onChangeIdentityVariations={(identityVariations) => {
                      this.setState({ identityVariations });
                  }}
                  environmentFlag={this.props.environmentFlag}
                  projectFlag={projectFlag}
                  onValueChange={(e) => {
                      this.setState({ initial_value: Utils.getTypedValue(Utils.safeParseEventValue(e)) });
                  }}
                  onCheckedChange={default_enabled => this.setState({ default_enabled })}
                />
                {!isEdit && !identity && Settings(projectAdmin)}
            </>
        );
        return (
            <ProjectProvider
              id={this.props.projectId}
            >
                {({ project }) => (
                    <Provider onSave={() => {
                        if (!isEdit || identity) {
                            this.close();
                        }
                        AppActions.getFeatures(this.props.projectId, this.props.environmentId, true);
                    }}
                    >
                        {({ isLoading, isSaving, error, influxData }, { createFlag, editFlagSettings, editFlagValue, editFlagSegments, createChangeRequest }) => {
                            const saveFeatureValue = (schedule) => {
                                if (is4Eyes || schedule) {
                                    openModal2(this.props.changeRequest ? 'Update Change Request' : 'New Change Request', <ChangeRequestModal
                                      showAssignees={is4Eyes}
                                      changeRequest={this.props.changeRequest}
                                      onSave={({
                                          title, description, approvals, live_from,
                                      }) => {
                                          closeModal2();
                                          this.save((projectId, environmentId, flag, projectFlag, environmentFlag, segmentOverrides) => {
                                              createChangeRequest(projectId, environmentId, flag, projectFlag, environmentFlag, segmentOverrides, {
                                                  id: this.props.changeRequest && this.props.changeRequest.id,
                                                  featureStateId: this.props.changeRequest && this.props.changeRequest.feature_states[0].id,
                                                  title,
                                                  description,
                                                  approvals,
                                                  live_from,
                                                  multivariate_options: this.props.multivariate_options ? (
                                                      this.props.multivariate_options.map((v) => {
                                                          const matching = this.state.multivariate_options.find(m => m.id === v.multivariate_feature_option);
                                                          return {
                                                              ...v,
                                                              percentage_allocation: matching.default_percentage_allocation,
                                                          };
                                                      })

                                                  ) : this.state.multivariate_options,
                                              }, !is4Eyes);
                                          });
                                      }}
                                    />);
                                } else if (document.getElementById('language-validation-error')) {
                                    openConfirm('Validation error', 'Your remote config value does not pass validation for the language you have selected. Are you sure you wish to save?', () => {
                                        this.save(editFlagValue, isSaving);
                                    }, null, 'Save', 'Cancel');
                                } else {
                                    this.save(editFlagValue, isSaving);
                                }
                            };

                            const saveSettings = () => {
                                this.save(editFlagSettings, isSaving);
                            };

                            const saveFeatureSegments = () => {
                                this.save(editFlagSegments, isSaving);
                            };

                            const createFeature = () => {
                                this.save(createFlag, isSaving);
                            };

                            return (

                                <Permission level="project" permission="ADMIN" id={this.props.projectId}>
                                    {({ permission: projectAdmin }) => (
                                        <div
                                          id="create-feature-modal"
                                        >
                                            {isEdit && !identity ? (
                                                <Tabs value={this.state.tab} onChange={tab => this.setState({ tab })}>
                                                    <TabItem data-test="value" tabLabel="Value">
                                                        <FormGroup className="mr-3 ml-3">
                                                            <Panel title={(
                                                                <Tooltip
                                                                  title={<h6 className="mb-0">Environment Value <span className="icon ion-ios-information-circle"/></h6>}
                                                                  place="top"
                                                                >
                                                                    {Constants.strings.ENVIRONMENT_OVERRIDE_DESCRIPTION(_.find(project.environments, { api_key: this.props.environmentId }).name)}
                                                                </Tooltip>
                                                    )}
                                                            >
                                                                {Value(projectAdmin)}
                                                            </Panel>
                                                            <p className="text-right mt-4">
                                                                {is4Eyes ? 'This will create a change request for the environment' : 'This will update the feature value for the environment'}
                                                                {' '}
                                                                <strong>
                                                                    {
                                                                _.find(project.environments, { api_key: this.props.environmentId }).name
                                                            }
                                                                </strong>
                                                            </p>
                                                            <div className="text-right">
                                                                {this.props.hasFeature('scheduling') && !is4Eyes && (
                                                                    <>
                                                                        {canSchedule ? (
                                                                            <ButtonOutline
                                                                              onClick={saveFeatureValue} className="mr-2" type="button"
                                                                              data-test="create-change-request"
                                                                              id="create-change-request-btn" disabled={isSaving || !name || invalid}
                                                                            >
                                                                                {isSaving ? existingChangeRequest ? 'Scheduling Update' : 'Schedule Update' : existingChangeRequest ? 'Update Change Request' : 'Schedule Update'}
                                                                            </ButtonOutline>
                                                                        ) : (
                                                                            <Tooltip title={(
                                                                                <ButtonOutline
                                                                                  disabled
                                                                                  onClick={saveFeatureValue} className="mr-2" type="button"
                                                                                  data-test="create-change-request"
                                                                                  id="create-change-request-btn"
                                                                                >
                                                                                    {isSaving ? existingChangeRequest ? 'Scheduling Update' : 'Schedule Update' : existingChangeRequest ? 'Update Change Request' : 'Schedule Update'}
                                                                                </ButtonOutline>
                                                                            )}
                                                                            >
                                                                                {'This feature is available on our scale-up plan'}
                                                                            </Tooltip>
                                                                        )}
                                                                    </>

                                                                )}
                                                                {is4Eyes ? (
                                                                    <Button
                                                                      onClick={saveFeatureValue} type="button" data-test="update-feature-btn"
                                                                      id="update-feature-btn" disabled={isSaving || !name || invalid}
                                                                    >
                                                                        {isSaving ? existingChangeRequest ? 'Updating Change Request' : 'Creating Change Request' : existingChangeRequest ? 'Update Change Request' : 'Create Change Request'}
                                                                    </Button>
                                                                ) : (
                                                                    <Button
                                                                      onClick={() => saveFeatureValue()} type="button" data-test="update-feature-btn"
                                                                      id="update-feature-btn" disabled={isSaving || !name || invalid}
                                                                    >
                                                                        {isSaving ? 'Updating' : 'Update Feature Value'}
                                                                    </Button>
                                                                )}


                                                            </div>
                                                        </FormGroup>
                                                    </TabItem>
                                                    {!existingChangeRequest && (
                                                    <TabItem data-test="segment_overrides" tabLabel="Segment Overrides">
                                                        {!identity && isEdit && (
                                                        <FormGroup className="mb-4 mr-3 ml-3">
                                                            <Permission level="environment" permission={Utils.getManageFeaturePermission()} id={this.props.environmentId}>
                                                                {({ permission: environmentAdmin }) => (environmentAdmin ? (
                                                                    <div>
                                                                        <Panel
                                                                          icon="ion-ios-settings"
                                                                          title={(
                                                                              <Tooltip
                                                                                title={<h6 className="mb-0">Segment Overrides <span className="icon ion-ios-information-circle"/></h6>}
                                                                                place="right"
                                                                              >
                                                                                  {Constants.strings.SEGMENT_OVERRIDES_DESCRIPTION}
                                                                              </Tooltip>
                                                                            )}
                                                                          action={
                                                                                (
                                                                                    <Button onClick={() => this.changeSegment(this.props.segmentOverrides)} type="button" className={`btn--outline${enabledSegment ? '' : '-red'}`}>
                                                                                        {enabledSegment ? 'Enable All' : 'Disable All'}
                                                                                    </Button>
                                                                                )
                                                                            }
                                                                        >
                                                                            {this.props.segmentOverrides ? (
                                                                                <SegmentOverrides
                                                                                  feature={projectFlag.id}
                                                                                  projectId={this.props.projectId}
                                                                                  multivariateOptions={multivariate_options}
                                                                                  environmentId={this.props.environmentId}
                                                                                  value={this.props.segmentOverrides}
                                                                                  controlValue={initial_value}
                                                                                  segments={this.props.segments}
                                                                                  onChange={this.props.updateSegments}
                                                                                />
                                                                            ) : (
                                                                                <div className="text-center">
                                                                                    <Loader/>
                                                                                </div>
                                                                            )}
                                                                        </Panel>
                                                                        <p className="text-right mt-4">
                                                                            {is4Eyes && is4EyesSegmentOverrides ? 'This will create a change request for the environment' : 'This will update the segment overrides for the environment'}
                                                                            {' '}
                                                                            <strong>
                                                                                {
                                                                                    _.find(project.environments, { api_key: this.props.environmentId }).name
                                                                                }
                                                                            </strong>
                                                                        </p>
                                                                        <div className="text-right">
                                                                            <Button
                                                                              onClick={saveFeatureSegments} type="button" data-test="update-feature-segments-btn"
                                                                              id="update-feature-segments-btn" disabled={isSaving || !name || invalid}
                                                                            >
                                                                                {isSaving ? 'Updating' : 'Update Segment Overrides'}
                                                                            </Button>
                                                                        </div>

                                                                    </div>

                                                                ) : (
                                                                    <Panel
                                                                      icon="ion-ios-settings"
                                                                      title={(
                                                                          <Tooltip
                                                                            title={<h6 className="mb-0">Segment Overrides <span className="icon ion-ios-information-circle"/></h6>}
                                                                            place="right"
                                                                          >
                                                                              {Constants.strings.SEGMENT_OVERRIDES_DESCRIPTION}
                                                                          </Tooltip>
                                                                        )}
                                                                    >
                                                                        <div dangerouslySetInnerHTML={{ __html: Constants.environmentPermissions(Utils.getManageFeaturePermission()) }}/>
                                                                    </Panel>
                                                                ))}
                                                            </Permission>
                                                        </FormGroup>
                                                        )}
                                                    </TabItem>
                                                    )}

                                                    {
                                                !identity
                                                && isEdit && !existingChangeRequest && (
                                                    <TabItem data-test="identity_overrides" tabLabel="Identity Overrides">
                                                        <FormGroup className="mb-4 mr-3 ml-3">
                                                            <PanelSearch
                                                              id="users-list"
                                                              title={(
                                                                  <Tooltip
                                                                    title={<h6 className="mb-0">Identity Overrides <span className="icon ion-ios-information-circle"/></h6>}
                                                                    place="right"
                                                                  >
                                                                      {Constants.strings.IDENTITY_OVERRIDES_DESCRIPTION}
                                                                  </Tooltip>
                                                                )}
                                                              action={
                                                                    (
                                                                        <Button onClick={() => this.changeIdentity(this.state.userOverrides)} type="button" className={`btn--outline${enabledIndentity ? '' : '-red'}`}>
                                                                            {enabledIndentity ? 'Enable All' : 'Disable All'}
                                                                        </Button>
                                                                    )
                                                                }
                                                              icon="ion-md-person"
                                                              items={this.state.userOverrides}
                                                              paging={this.state.userOverridesPaging}
                                                              nextPage={() => this.userOverridesPage(this.state.userOverridesPaging.currentPage + 1)}
                                                              prevPage={() => this.userOverridesPage(this.state.userOverridesPaging.currentPage - 1)}
                                                              goToPage={page => this.userOverridesPage(page)}
                                                              searchPanel={
                                                                    (
                                                                        <div className="text-center mt-2 mb-2">
                                                                            <IdentityListProvider>
                                                                                {({ isLoading, identities }) => (
                                                                                    <Flex className="text-left">
                                                                                        <Select
                                                                                          onInputChange={this.onSearchIdentityChange}
                                                                                          data-test="select-identity"
                                                                                          placeholder="Create an Identity Override..."
                                                                                          value={this.state.selectedIdentity}
                                                                                          onChange={selectedIdentity => this.setState({ selectedIdentity }, this.addItem)}
                                                                                          options={this.identityOptions(identities, this.state.userOverrides, isLoading)}
                                                                                          styles={{
                                                                                              control: base => ({
                                                                                                  ...base,
                                                                                                  '&:hover': { borderColor: '$bt-brand-secondary' },
                                                                                                  border: '1px solid $bt-brand-secondary',
                                                                                              }),
                                                                                          }}
                                                                                        />
                                                                                    </Flex>
                                                                                )}
                                                                            </IdentityListProvider>
                                                                        </div>
                                                                    )
                                                                }
                                                              renderRow={({ id, feature_state_value, enabled, identity }) => (
                                                                  <Row
                                                                    onClick={() => {
                                                                        window.open(`${document.location.origin}/project/${this.props.projectId}/environment/${this.props.environmentId}/users/${identity.identifier}/${identity.id}?flag=${projectFlag.name}`, '_blank');
                                                                    }} space className="list-item cursor-pointer"
                                                                    key={id}
                                                                  >
                                                                      <Flex>
                                                                          {identity.identifier}
                                                                      </Flex>
                                                                      <Switch disabled checked={enabled}/>
                                                                      <div className="ml-2">
                                                                          {feature_state_value && (
                                                                          <FeatureValue
                                                                            value={feature_state_value}
                                                                          />
                                                                          )}
                                                                      </div>


                                                                      <a
                                                                        target="_blank"
                                                                        href={`/project/${this.props.projectId}/environment/${this.props.environmentId}/users/${identity.identifier}/${identity.id}?flag=${projectFlag.name}`}
                                                                        className="ml-2 btn btn-link btn--link" onClick={() => {
                                                                        }}
                                                                      >
                                                                            Edit
                                                                      </a>
                                                                  </Row>
                                                              )}
                                                              renderNoResults={(
                                                                  <Panel
                                                                    id="users-list"
                                                                    title={(
                                                                        <Tooltip
                                                                          title={<h6 className="mb-0">Identity Overrides <span className="icon ion-ios-information-circle"/></h6>}
                                                                          place="right"
                                                                        >
                                                                            {Constants.strings.IDENTITY_OVERRIDES_DESCRIPTION}
                                                                        </Tooltip>
                                                                        )}
                                                                  >
                                                                      { (
                                                                          <IdentityListProvider>
                                                                              {({ isLoading, identities }) => (
                                                                                  <div>
                                                                                      <Flex className="text-left">
                                                                                          <Select
                                                                                            data-test="select-identity"
                                                                                            placeholder="Search"
                                                                                            onInputChange={this.onSearchIdentityChange}
                                                                                            value={this.state.selectedIdentity}
                                                                                            onChange={selectedIdentity => this.setState({ selectedIdentity }, this.addItem)}
                                                                                            options={this.identityOptions(identities, this.state.userOverrides, isLoading)}
                                                                                            styles={{
                                                                                                control: base => ({
                                                                                                    ...base,
                                                                                                    '&:hover': { borderColor: '$bt-brand-secondary' },
                                                                                                    border: '1px solid $bt-brand-secondary',
                                                                                                }),
                                                                                            }}
                                                                                          />
                                                                                      </Flex>
                                                                                      <div className="mt-2">
                                                                                            No identities are overriding this feature.
                                                                                      </div>
                                                                                  </div>
                                                                              )}
                                                                          </IdentityListProvider>
                                                                        )}
                                                                  </Panel>
                                                                )}
                                                              isLoading={!this.state.userOverrides}
                                                            />
                                                        </FormGroup>
                                                    </TabItem>
                                                )
                                            }
                                                    { !existingChangeRequest && !projectOverrides.disableInflux && (this.props.hasFeature('flag_analytics') && this.props.flagId) && (
                                                    <TabItem data-test="analytics" tabLabel="Analytics">
                                                        <FormGroup className="mb-4 mr-3 ml-3">
                                                            <Panel
                                                              title={<h6 className="mb-0">Flag events for last {this.state.period}</h6>}
                                                            >
                                                                {this.drawChart(influxData)}
                                                            </Panel>
                                                        </FormGroup>
                                                    </TabItem>
                                                    )}
                                                    {!existingChangeRequest && (
                                                    <TabItem data-test="settings" tabLabel="Settings">
                                                        {Settings(projectAdmin)}
                                                        {isEdit && (
                                                        <div className="text-right">
                                                            {!projectAdmin ? (
                                                                <p className="text-right">
                                                                    To edit this feature's settings, you will need <strong>Project Administrator permissions</strong>. Please contact your project administrator.
                                                                </p>
                                                            ) : (
                                                                <p className="text-right">
                                                                    This will save the above settings <strong>all environments</strong>.
                                                                </p>
                                                            )}

                                                            {!!projectAdmin && (
                                                                <Button
                                                                  onClick={saveSettings} data-test="update-feature-btn" id="update-feature-btn"
                                                                  disabled={(isSaving || !name || invalid)}
                                                                >
                                                                    {isSaving ? 'Updating' : 'Update Settings'}
                                                                </Button>
                                                            )}

                                                        </div>
                                                        )}
                                                    </TabItem>
                                                    )}
                                                </Tabs>
                                            ) : (
                                                <div>
                                                    {Value(projectAdmin)}
                                                    {!identity && (
                                                    <div className="text-right">
                                                        <p className="text-right">
                                                        This will create the feature for <strong>all environments</strong>, you can edit this feature per environment once the feature is created.
                                                        </p>
                                                        <Button
                                                          onClick={createFeature} data-test="create-feature-btn" id="create-feature-btn"
                                                          disabled={isSaving || !name || invalid}
                                                        >
                                                            {isSaving ? 'Creating' : 'Create Feature'}
                                                        </Button>
                                                    </div>
                                                    )}

                                                </div>
                                            )}

                                            {error && <Error error={error}/>}
                                            {identity && (
                                            <div className="pr-3">
                                                {identity ? (
                                                    <div className="mb-3">
                                                        <p className="text-left ml-3">
                                                        This will update the feature value for the user
                                                            {' '}
                                                            <strong>{identityName}</strong>
                                                            {' '}
                                                        in
                                                            <strong>
                                                                {' '}
                                                                {
                                                                _.find(project.environments, { api_key: this.props.environmentId }).name
                                                            }.
                                                            </strong>
                                                            {' Any segment overrides for this feature will now be ignored.'}
                                                        </p>
                                                    </div>
                                                ) : ''}

                                                <div className="text-right mb-2">
                                                    {identity && (
                                                    <div>
                                                        <Button
                                                          onClick={() => saveFeatureValue()} data-test="update-feature-btn" id="update-feature-btn"
                                                          disabled={isSaving || !name || invalid}
                                                        >
                                                            {isSaving ? 'Updating' : 'Update Feature'}
                                                        </Button>
                                                    </div>
                                                    )}
                                                </div>
                                            </div>
                                            )}
                                        </div>
                                    )}
                                </Permission>
                            );
                        }}

                    </Provider>
                )}
            </ProjectProvider>
        );
    }
};

CreateFlag.propTypes = {};

module.exports = ConfigProvider(withSegmentOverrides(CreateFlag));
