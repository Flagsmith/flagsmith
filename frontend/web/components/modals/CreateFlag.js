import React, { Component } from 'react';
import { BarChart, ResponsiveContainer, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend } from 'recharts';
import Tabs from '../base/forms/Tabs';
import TabItem from '../base/forms/TabItem';
import withSegmentOverrides from '../../../common/providers/withSegmentOverrides';
import data from '../../../common/data/base/_data';
import SegmentOverrides from '../SegmentOverrides';
import AddEditTags from '../AddEditTags';
import Constants from '../../../common/constants';
import _data from '../../../common/data/base/_data';
import ValueEditor from '../ValueEditor';
import VariationValue from '../mv/VariationValue';
import AddVariationButton from '../mv/AddVariationButton';
import VariationOptions from '../mv/VariationOptions';
import FlagOwners from '../FlagOwners';

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
                        const matchingVariation = this.props.environmentVariations.find(e => e.multivariate_feature_option === v.id);
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
            _data.post(`${Project.api}environments/${environmentId}/identities/${selectedIdentity}/featurestates/`, {
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
            openConfirm('Please confirm', 'This will remove the variation on your feature for all environments, if you wish to turn it off just for this environment you can set the % value to 0.', () => {
                const idToRemove = this.state.multivariate_options[i].id;
                if (idToRemove) {
                    this.props.removeMultiVariateOption(idToRemove);
                }
                this.state.multivariate_options.splice(i, 1);
                this.forceUpdate();
            });
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
        const controlValue = Utils.calculateControl(multivariate_options, environmentVariations);
        const valueString = identity ? 'User override' : !!multivariate_options && multivariate_options.length ? `Control Value - ${controlValue}%` : `Value (optional)${' - these can be set per environment'}`;
        const enabledString = isEdit ? 'Enabled' : 'Enabled by default';
        const environmentVariations = this.props.environmentVariations;

        const invalid = !!multivariate_options && multivariate_options.length && controlValue < 0;
        const Settings = (
            <>
                {!identity && this.state.tags && (
                    <FormGroup className="mb-4 mr-3 ml-3" >
                        <InputGroup
                          title={identity ? 'Tags' : 'Tags (optional)'}
                          tooltip={Constants.strings.TAGS_DESCRIPTION}
                          component={(
                              <AddEditTags
                                readOnly={!!identity} projectId={this.props.projectId} value={this.state.tags}
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
                          readOnly: !!identity,
                          name: 'featureDesc',
                      }}
                      onChange={e => this.setState({ description: Utils.safeParseEventValue(e) })}
                      isValid={name && name.length}
                      type="text" title={identity ? 'Description' : 'Description (optional)'}
                      placeholder="e.g. 'This determines what size the header is' "
                    />
                </FormGroup>
                {!identity && isEdit && (
                    <FormGroup className="mb-4 mr-3 ml-3" >
                        <InputGroup
                          value={description}
                          component={(
                              <Switch checked={this.state.is_archived} onChange={is_archived => this.setState({ is_archived })}/>
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
        const Value = (
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
                <FormGroup className="mb-4 mr-3 ml-3">
                    <div>
                        <label>{enabledString}</label>
                    </div>
                    <Switch
                      data-test="toggle-feature-button"
                      defaultChecked={default_enabled}
                      disabled={hide_from_client}
                      checked={!hide_from_client && default_enabled}
                      onChange={default_enabled => this.setState({ default_enabled })}
                    />
                </FormGroup>

                {!(!!identity && (multivariate_options && !!multivariate_options.length)) && (
                    <FormGroup className="mx-3 mb-4 mr-3">
                        <InputGroup
                          component={(
                              <ValueEditor
                                data-test="featureValue"
                                name="featureValue" className="full-width"
                                value={`${typeof initial_value === 'undefined' || initial_value === null ? '' : initial_value}`}
                                onChange={e => this.setState({ initial_value: Utils.getTypedValue(Utils.safeParseEventValue(e)) })}
                                disabled={hide_from_client}
                                placeholder="e.g. 'big' "
                              />
                            )}
                          tooltip={Constants.strings.REMOTE_CONFIG_DESCRIPTION}
                          title={`${valueString}`}
                        />
                    </FormGroup>
                ) }

                {!!identity && (
                    <div>
                        <FormGroup className="mb-4 mx-3">
                            <VariationOptions
                              disabled
                              select
                              controlValue={this.props.environmentFlag.feature_state_value}
                              variationOverrides={this.state.identityVariations}
                              setVariations={(identityVariations) => {
                                  this.setState({ identityVariations });
                              }}
                              updateVariation={() => {}}
                              weightTitle="Override Weight %"
                              multivariateOptions={projectFlag.multivariate_options}
                              removeVariation={() => {}}
                            />
                        </FormGroup>
                    </div>
                )}
                {!identity && (
                    <div>
                        <FormGroup className="ml-3 mb-4 mr-3">
                            {(!!environmentVariations || !isEdit) && (
                                <VariationOptions
                                  disabled={!!identity}
                                  controlValue={controlValue}
                                  variationOverrides={environmentVariations}
                                  updateVariation={this.updateVariation}
                                  weightTitle={isEdit ? 'Environment Weight %' : 'Default Weight %'}
                                  multivariateOptions={multivariate_options}
                                  removeVariation={this.removeVariation}
                                />
                            )}

                        </FormGroup>
                        <AddVariationButton onClick={this.addVariation}/>
                    </div>

                )}
                {!isEdit && !identity && Settings}
            </>
        );
        return (
            <ProjectProvider
              id={this.props.projectId}
            >
                {({ project }) => (
                    <Provider onSave={() => {
                        this.close();
                        AppActions.getFeatures(this.props.projectId, this.props.environmentId, true);
                    }}
                    >
                        {({ isLoading, isSaving, error, influxData }, { createFlag, editFlag }) => (
                            <form
                              id="create-feature-modal"
                              onSubmit={(e) => {
                                  e.stopPropagation();
                                  e.preventDefault();
                                  const func = isEdit ? editFlag : createFlag;
                                  this.save(func, isSaving);
                              }}
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
                                                    {Value}
                                                </Panel>
                                            </FormGroup>
                                        </TabItem>
                                        <TabItem data-test="overrides" tabLabel="Overrides">
                                            {!identity && isEdit && (
                                                <Permission level="project" permission="ADMIN" id={this.props.projectId}>
                                                    {({ permission: projectAdmin }) => projectAdmin && (

                                                        <FormGroup className="mb-4 mr-3 ml-3">
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
                                                        </FormGroup>
                                                    )}
                                                </Permission>
                                            )}
                                            {
                                                !identity
                                                && isEdit && (
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
                                                                                       placeholder="Search"
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
                                                )
                                            }
                                        </TabItem>
                                        { !projectOverrides.disableInflux && (this.props.hasFeature('flag_analytics') && this.props.flagId) && (
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

                                        <TabItem data-test="settings" tabLabel="Settings">
                                            {Settings}
                                        </TabItem>
                                    </Tabs>
                                ) : (
                                    Value
                                )}

                                {error && <Error error={error}/>}
                                <div className={identity ? 'pr-3' : 'side-modal__footer pr-5'}>
                                    <div className="mb-3">
                                        {identity ? (
                                            <p className="text-right">
                                                This will update the feature value for the
                                                user
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
                                                <br/>
                                                {'Any segment overrides for this feature will now be ignored.'}
                                            </p>
                                        ) : isEdit ? (
                                            <p className="text-right">
                                                This will update the feature value for the environment
                                                {' '}
                                                <strong>
                                                    {
                                                        _.find(project.environments, { api_key: this.props.environmentId }).name
                                                    }
                                                </strong>
                                            </p>
                                        ) : (
                                            <p className="text-right">
                                              This will create the feature for <strong>all environments</strong>, you can edit this feature per environment once the feature is created.
                                            </p>
                                        )}

                                    </div>
                                    <div className="text-right mb-2">
                                        {isEdit ? (
                                            <Button data-test="update-feature-btn" id="update-feature-btn" disabled={isSaving || !name || invalid}>
                                                {isSaving ? 'Updating' : 'Update Feature'}
                                            </Button>
                                        ) : (
                                            <Button data-test="create-feature-btn" id="create-feature-btn" disabled={isSaving || !name}>
                                                {isSaving ? 'Creating' : 'Create Feature'}
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </form>
                        )}

                    </Provider>
                )}
            </ProjectProvider>
        );
    }
};

CreateFlag.propTypes = {};

module.exports = ConfigProvider(withSegmentOverrides(CreateFlag));
