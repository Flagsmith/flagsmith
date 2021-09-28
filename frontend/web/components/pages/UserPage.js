import React, { Component } from 'react';
import ConfirmToggleFeature from '../modals/ConfirmToggleFeature';
import ConfirmRemoveFeature from '../modals/ConfirmRemoveFeature';
import CreateFlagModal from '../modals/CreateFlag';
import CreateTraitModal from '../modals/CreateTrait';
import TryIt from '../TryIt';
import CreateSegmentModal from '../modals/CreateSegment';

const returnIfDefined = (value, value2) => {
    if (value === null || value === undefined) {
        return value2;
    }
    return value;
};
const valuesEqual = (actualValue, flagValue) => {
    const nullFalseyA = actualValue == null || actualValue === '' || typeof actualValue === 'undefined';
    const nullFalseyB = flagValue == null || flagValue === '' || typeof flagValue === 'undefined';
    if (nullFalseyA && nullFalseyB) {
        return true;
    }
    return actualValue == flagValue;
};
const UserPage = class extends Component {
    static displayName = 'UserPage'

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    componentDidMount() {
        AppActions.getIdentity(this.props.match.params.environmentId, this.props.match.params.id);
        AppActions.getIdentitySegments(this.props.match.params.projectId, this.props.match.params.id);
        AppActions.getFeatures(this.props.match.params.projectId, this.props.match.params.environmentId);
        this.getActualFlags();
        API.trackPage(Constants.pages.USER);
    }

    onSave = () => {
        this.getActualFlags();
    }


    editSegment = (segment) => {
        API.trackEvent(Constants.events.VIEW_SEGMENT);
        openModal('Edit Segment', <CreateSegmentModal
          segment={segment}
          isEdit
          environmentId={this.props.match.params.environmentId}
          projectId={this.props.match.params.projectId}
          projectFlag={segment}
        />, null, { className: 'alert fade expand create-segment-modal' });
    };


    getActualFlags = () => {
        const url = `${Project.api}identities/?identifier=${this.props.match.params.identity}`;
        fetch(url, {
            headers: { 'X-Environment-Key': this.props.match.params.environmentId },
        }).then(res => res.json()).then((res) => {
            this.setState({ actualFlags: _.keyBy(res.flags, v => v.feature.name) });
        }).catch((err) => {
        });
    }

    onTraitSaved = () => {
        AppActions.getIdentitySegments(this.props.match.params.projectId, this.props.match.params.id);
    }

    confirmToggle = (projectFlag, environmentFlag, cb) => {
        openModal('Toggle Feature', <ConfirmToggleFeature
          identity={this.props.match.params.id}
          identityName={decodeURIComponent(this.props.match.params.identity)}
          environmentId={this.props.match.params.environmentId}
          projectFlag={projectFlag}
          environmentFlag={environmentFlag}
          cb={cb}
        />);
    }

    editFlag = (projectFlag, environmentFlag, identityFlag, multivariate_feature_state_values) => {
        API.trackEvent(Constants.events.VIEW_USER_FEATURE);
        openModal(`Edit User Feature: ${projectFlag.name}`, <CreateFlagModal
          isEdit
          identity={this.props.match.params.id}
          identityName={decodeURIComponent(this.props.match.params.identity)}
          environmentId={this.props.match.params.environmentId}
          projectId={this.props.match.params.projectId}
          projectFlag={projectFlag}
          identityFlag={{
              ...identityFlag,
              multivariate_feature_state_values
          }}
          environmentFlag={environmentFlag}
        />);
    };

    createTrait = () => {
        API.trackEvent(Constants.events.VIEW_USER_FEATURE);
        openModal('Create User Trait', <CreateTraitModal
          isEdit={false}
          onSave={this.onTraitSaved}
          identity={this.props.match.params.id}
          identityName={decodeURIComponent(this.props.match.params.identity)}
          environmentId={this.props.match.params.environmentId}
          projectId={this.props.match.params.projectId}
        />);
    };

    editTrait = (trait) => {
        API.trackEvent(Constants.events.VIEW_USER_FEATURE);
        openModal('Edit User Trait', <CreateTraitModal
          isEdit
          {...trait}
          onSave={this.onTraitSaved}
          identity={this.props.match.params.id}
          identityName={decodeURIComponent(this.props.match.params.identity)}
          environmentId={this.props.match.params.environmentId}
          projectId={this.props.match.params.projectId}
        />);
    };

    confirmRemove = (projectFlag, cb, identity) => {
        openModal('Reset User Feature', <ConfirmRemoveFeature
          identity={identity}
          environmentId={this.props.match.params.environmentId}
          projectFlag={projectFlag}
          cb={cb}
        />);
    }

    removeTrait = (id, trait_key) => {
        openConfirm(
            <h3>Delete Trait</h3>,
            <p>
                {'Are you sure you want to delete trait '}
                <strong>{trait_key}</strong>
                {' from this user?'}
            </p>,
            () => AppActions.deleteIdentityTrait(this.props.match.params.environmentId, this.props.match.params.id, id),
        );
    }

    render() {
        const { hasFeature } = this.props;
        const { actualFlags } = this.state;
        const preventAddTrait = !AccountStore.getOrganisation().persist_trait_data;
        return (
            <div className="app-container">
                <IdentityProvider onSave={this.onSave}>
                    {({ isSaving, isLoading, error, environmentFlags, projectFlags, traits, identityFlags, identity }, { toggleFlag, removeFlag, editFlag }) => (isLoading || !identityFlags || !actualFlags || !projectFlags
                        ? <div className="text-center"><Loader/></div> : (
                            <div className="container">
                                <div className="row">
                                    <div className="col-md-12">
                                        <h3>
                                            {(identity && identity.identity.identifier) || this.props.match.params.id}
                                        </h3>
                                        <p>
                                            View and manage feature states and traits for this user. This will override
                                            any feature
                                            states you have for your current environment for this user only. Any
                                            features that are not overriden for this user will fallback to the
                                            environment defaults.
                                        </p>
                                        <FormGroup>
                                            <FormGroup>
                                                <PanelSearch
                                                  id="user-features-list"
                                                  className="no-pad"
                                                  itemHeight={70}
                                                  icon="ion-ios-rocket"
                                                  title="Features"
                                                  items={projectFlags}
                                                  sorting={[
                                                      { label: 'Name', value: 'name', order: 'asc', default: true },
                                                      { label: 'Created Date', value: 'created_date', order: 'asc' },
                                                  ]}
                                                  renderRow={({ name, id, enabled, created_date, feature, type }, i) => {
                                                      const identityFlag = identityFlags[id] || {};
                                                      const environmentFlag = environmentFlags[id];
                                                      const hasUserOverride = identityFlag.identity;
                                                      const flagEnabled = hasUserOverride
                                                          ? identityFlag.enabled
                                                          : environmentFlag.enabled; // show default value s
                                                      const flagValue = hasUserOverride ? identityFlag.feature_state_value
                                                          : environmentFlag.feature_state_value;

                                                      const actualEnabled = (actualFlags && !!actualFlags && actualFlags[name] && actualFlags[name].enabled) || false;
                                                      const actualValue = !!actualFlags && actualFlags[name] && actualFlags[name].feature_state_value;
                                                      const flagEnabledDifferent = (hasUserOverride ? false
                                                          : actualEnabled !== flagEnabled);
                                                      const flagValueDifferent = (hasUserOverride ? false : !valuesEqual(actualValue, flagValue));
                                                      const projectFlag = projectFlags && projectFlags.find(p => p.id === (environmentFlag && environmentFlag.feature));
                                                      const isMultiVariateOverride = flagValueDifferent && projectFlag && projectFlag.multivariate_options && projectFlag.multivariate_options.find((v) => {
                                                          const value = Utils.featureStateToValue(v);
                                                          return value === actualValue;
                                                      });
                                                      const flagDifferent = flagEnabledDifferent || flagValueDifferent;
                                                      return (
                                                          <Row
                                                            className={`list-item clickable ${flagDifferent && 'flag-different'}`} key={id} space
                                                            data-test={`user-feature-${i}`}
                                                          >
                                                              <div
                                                                onClick={() => this.editFlag(_.find(projectFlags, { id }), environmentFlags[id], actualFlags[name],identityFlags && identityFlags[id] && identityFlags[id].multivariate_feature_state_values)}
                                                                className="flex flex-1"
                                                              >
                                                                  <Row>
                                                                      <ButtonLink>
                                                                          {name}
                                                                      </ButtonLink>
                                                                  </Row>
                                                                  {hasUserOverride ? (
                                                                      <Row className="chip">
                                                                          <span>
                                                                            Overriding defaults
                                                                          </span>
                                                                          <span
                                                                            className="chip-icon icon ion-md-information"
                                                                          />
                                                                      </Row>

                                                                  ) : (
                                                                      flagEnabledDifferent ? (
                                                                          <span data-test={`feature-override-${i}`} className="flex-row chip">
                                                                              <Row>
                                                                                  <Flex>
                                                                                      {isMultiVariateOverride ? (
                                                                                          <span>
                                                                                              This flag is being overridden by a variation defined on your feature, the control value is <strong>{flagEnabled ? 'on' : 'off'}</strong> for this user
                                                                                          </span>
                                                                                      ) : (
                                                                                          <span>
                                                                                              This flag is being overridden by segments and would normally be <strong>{flagEnabled ? 'on' : 'off'}</strong> for this user
                                                                                          </span>
                                                                                      )}

                                                                                  </Flex>
                                                                                  <span
                                                                                      className="ml-1 chip-icon icon ion-md-information"
                                                                                  />
                                                                              </Row>


                                                                          </span>
                                                                      ) : flagValueDifferent ? isMultiVariateOverride ? (
                                                                          <span data-test={`feature-override-${i}`} className="flex-row chip">
                                                                              <span>
                                                                              This feature is being overriden by a % variation in the environment, the control value of this feature is  <FeatureValue
                                                                                data-test={`user-feature-original-value-${i}`}
                                                                                value={`${flagValue}`}
                                                                              />
                                                                              </span>
                                                                              <span
                                                                                className="chip-icon icon ion-md-information"
                                                                              />
                                                                          </span>
                                                                      ) : (
                                                                          <span data-test={`feature-override-${i}`} className="flex-row chip">
                                                                              <span>
                                                                              This feature is being overriden by segments and would normally be <FeatureValue
                                                                                data-test={`user-feature-original-value-${i}`}
                                                                                value={`${flagValue}`}
                                                                              /> for this user
                                                                              </span>
                                                                              <span
                                                                                className="chip-icon icon ion-md-information"
                                                                              />
                                                                          </span>
                                                                      ) : (
                                                                          <div className="list-item-footer">
                                                                              <span className="faint">
                                                                              Using environment defaults
                                                                              </span>
                                                                          </div>
                                                                      )
                                                                  )}
                                                              </div>
                                                              <Row>
                                                                  <Column>
                                                                      <div className="feature-value">
                                                                          <FeatureValue
                                                                            data-test={`user-feature-value-${i}`}
                                                                            value={actualValue}
                                                                          />
                                                                      </div>
                                                                  </Column>
                                                                  <Column>
                                                                      <div>
                                                                          <Switch
                                                                            data-test={`user-feature-switch-${i}${actualEnabled ? '-on' : '-off'}`}
                                                                            checked={actualEnabled}
                                                                            onChange={() => this.confirmToggle(_.find(projectFlags, { id }), environmentFlags[id], (environments) => {
                                                                                toggleFlag({
                                                                                    environmentId: this.props.match.params.environmentId,
                                                                                    identity: this.props.match.params.id,
                                                                                    projectFlag: { id },
                                                                                    environmentFlag: environmentFlags[id],
                                                                                    identityFlag,
                                                                                });
                                                                            })}
                                                                          />
                                                                      </div>
                                                                  </Column>
                                                                  {hasUserOverride && (
                                                                  <Column>
                                                                      <Button
                                                                        onClick={() => this.confirmRemove(_.find(projectFlags, { id }), () => {
                                                                            removeFlag({
                                                                                environmentId: this.props.match.params.environmentId,
                                                                                identity: this.props.match.params.id,
                                                                                identityFlag,
                                                                            });
                                                                        }, identity.identity.identifier)}
                                                                      >
                                                                            Reset
                                                                      </Button>
                                                                  </Column>
                                                                  )}
                                                              </Row>
                                                          </Row>
                                                      );
                                                  }
                                                    }
                                                  renderNoResults={(
                                                      <Panel
                                                        icon="ion-ios-rocket"
                                                        title="Features"
                                                      >
                                                          <div className="text-center">
                                                              This user has no features yet.
                                                              {' '}
                                                              <br/>
                                                              When you start
                                                              {' '}
                                                              <Link
                                                                className="dark"
                                                                to={`project/${this.props.match.params.projectId}/environment/${this.props.match.params.environmentId}/features`}
                                                              >
                                                                  creating features
                                                              </Link>
                                                              {' '}
                                                              for your project you will set them per user here.
                                                          </div>

                                                      </Panel>
                                                    )}
                                                  filterRow={({ name }, search) => name.toLowerCase().indexOf(search) > -1}
                                                />
                                            </FormGroup>
                                            {!preventAddTrait && (
                                                <FormGroup>
                                                    <PanelSearch
                                                      id="user-traits-list"
                                                      className="no-pad"
                                                      icon="ion-ios-person"
                                                      itemHeight={65}
                                                      title="Traits"
                                                      items={traits}
                                                      renderFooter={() => (
                                                          <FormGroup className="text-center mb-2">
                                                              <Button id="add-trait" onClick={this.createTrait}>Add new trait</Button>
                                                          </FormGroup>
                                                      )}
                                                      renderRow={({ id, trait_value, trait_key }, i) => (
                                                          <Row
                                                            className="list-item clickable" key={trait_key}
                                                            space data-test={`user-trait-${i}`}
                                                          >
                                                              <div
                                                                onClick={() => this.editTrait({
                                                                    trait_value,
                                                                    trait_key,
                                                                })}
                                                                className="flex flex-1"
                                                              >
                                                                  <Row>
                                                                      <ButtonLink className={`js-trait-key-${i}`} href="#">
                                                                          {trait_key}
                                                                      </ButtonLink>
                                                                  </Row>
                                                              </div>
                                                              <Row>
                                                                  <Column>
                                                                      <FeatureValue
                                                                        data-test={`user-trait-value-${i}`}
                                                                        value={trait_value}
                                                                      />
                                                                  </Column>
                                                                  <Column>
                                                                      <button
                                                                        id="remove-feature"
                                                                        className="btn btn--with-icon"
                                                                        type="button"
                                                                        onClick={() => this.removeTrait(id, trait_key)}
                                                                        data-test={`delete-user-trait-${i}`}
                                                                      >
                                                                          <RemoveIcon/>
                                                                      </button>
                                                                  </Column>
                                                              </Row>
                                                          </Row>
                                                      )
                                                    }
                                                      renderNoResults={(
                                                          <Panel
                                                            icon="ion-ios-person"
                                                            title="Traits"
                                                          >
                                                              <div className="text-center">
                                                              This user has no traits.
                                                                  <FormGroup className="text-center mb-0 mt-2">
                                                                      <Button id="add-trait" onClick={this.createTrait}>Add new trait</Button>
                                                                  </FormGroup>
                                                              </div>
                                                          </Panel>
                                                    )}
                                                      filterRow={({ trait_key }, search) => trait_key.toLowerCase().indexOf(search) > -1}
                                                    />
                                                </FormGroup>
                                            )}
                                            <IdentitySegmentsProvider>
                                                {({ isLoading: segmentsLoading, segments }) => (segmentsLoading ? <div className="text-center"><Loader/></div> : (
                                                    <FormGroup>
                                                        <PanelSearch
                                                          id="user-segments-list"
                                                          className="no-pad"
                                                          icon="ion-ios-globe"
                                                          title="Segments"
                                                          itemHeight={70}
                                                          items={segments || []}
                                                          renderRow={({ name, id, enabled, created_date, type, description }, i) => (
                                                              <Row
                                                                onClick={() => this.editSegment(segments[i])}
                                                                className="list-item clickable"
                                                                space
                                                                key={i}
                                                              >
                                                                  <div
                                                                    className="flex flex-1"
                                                                  >
                                                                      <Row>
                                                                          <ButtonLink
                                                                            onClick={() => this.editSegment(segments[i])}
                                                                          >
                                                                              <span data-test={`segment-${i}-name`} className="bold-link">
                                                                                  {name}
                                                                              </span>
                                                                          </ButtonLink>
                                                                      </Row>
                                                                      <div className="list-item-footer faint mt-2">
                                                                          {description ? <div>{description}<br/></div> : ''}
                                                                        Created
                                                                          {' '}
                                                                          {moment(created_date).format('DD/MMM/YYYY')}
                                                                      </div>
                                                                  </div>
                                                              </Row>
                                                          )
                                                          }
                                                          renderNoResults={(
                                                              <Panel
                                                                icon="ion-ios-globe"
                                                                title="Segments"
                                                              >
                                                                  <div className="text-center">
                                                                      This user is not part of any segment.
                                                                  </div>
                                                              </Panel>
                                                          )}
                                                          filterRow={({ name }, search) => name.toLowerCase().indexOf(search) > -1}
                                                        />
                                                    </FormGroup>
                                                ))}
                                            </IdentitySegmentsProvider>
                                        </FormGroup>
                                    </div>
                                    <div className="col-md-12 mt-2">
                                        <FormGroup>
                                            <CodeHelp
                                              title="Managing user traits and segments"
                                              snippets={Constants.codeHelp.USER_TRAITS(this.props.match.params.environmentId, this.props.match.params.id)}
                                            />
                                        </FormGroup>
                                        <FormGroup>
                                            <TryIt
                                              title="Check to see what features and traits are coming back for this user"
                                              environmentId={this.props.match.params.environmentId}
                                              userId={(identity && identity.identity.identifier) || this.props.match.params.id}
                                            />
                                        </FormGroup>
                                    </div>
                                </div>
                            </div>
                        ))
                    }
                </IdentityProvider>
            </div>
        );
    }
};

UserPage.propTypes = {};

module.exports = ConfigProvider(UserPage);
