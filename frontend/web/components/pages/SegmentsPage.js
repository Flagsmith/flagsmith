import React, { Component } from 'react';
import CreateSegmentModal from '../modals/CreateSegment';
import TryIt from '../TryIt';
import ConfirmRemoveSegment from '../modals/ConfirmRemoveSegment';

const SegmentsPage = class extends Component {
    static displayName = 'SegmentsPage';

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props, context) {
        super(props, context);
        this.state = {};
        AppActions.getFeatures(this.props.match.params.projectId, this.props.match.params.environmentId);
        AppActions.getSegments(this.props.match.params.projectId, this.props.match.params.environmentId);
    }

    componentWillUpdate(newProps) {
        const { match: { params } } = newProps;
        const { match: { params: oldParams } } = this.props;
        if (params.environmentId != oldParams.environmentId || params.projectId != oldParams.projectId) {
            AppActions.getFeatures(this.props.match.params.projectId, this.props.match.params.environmentId);
            AppActions.getSegments(params.projectId, params.environmentId);
        }
    }

    componentDidMount = () => {
        API.trackPage(Constants.pages.FEATURES);
        const { match: { params } } = this.props;
        AsyncStorage.setItem('lastEnv', JSON.stringify({
            orgId: AccountStore.getOrganisation().id,
            projectId: params.projectId,
            environmentId: params.environmentId,
        }));
    };

    newSegment = (flags) => {
        openModal('New Segment', <CreateSegmentModal
          flags={flags}
          environmentId={this.props.match.params.environmentId}
          projectId={this.props.match.params.projectId}
        />, null, { className: 'alert fade expand create-segment-modal' });
    };


    editSegment = (segment, readOnly) => {
        API.trackEvent(Constants.events.VIEW_SEGMENT);
        openModal('Edit Segment', <CreateSegmentModal
          segment={segment}
          isEdit
          readOnly={readOnly}
          environmentId={this.props.match.params.environmentId}
          projectId={this.props.match.params.projectId}
          projectFlag={segment}
        />, null, { className: 'alert fade expand create-segment-modal' });
    };


    componentWillReceiveProps(newProps) {
        if (newProps.match.params.environmentId != this.props.match.params.environmentId) {
            AppActions.getSegments(newProps.match.params.projectId, newProps.match.params.environmentId);
        }
    }

    confirmRemove = (segment, cb) => {
        openModal('Remove Segment', <ConfirmRemoveSegment
          environmentId={this.props.match.params.environmentId}
          segment={segment}
          cb={cb}
        />);
    }

    onError = (error) => {
        // Kick user back out to projects
        this.context.router.history.replace('/projects');
    }


    createSegmentPermission(el, level, id, permissionText) {
        return (
            <Permission level="environment" permission="CREATE_SEGMENT" id={this.props.match.params.environmentId}>
                {({ permission, isLoading }) => (permission ? (
                    el(permission)
                ) : this.renderWithPermission(permission, level, el(permission)))}
            </Permission>
        );
    }

    renderWithPermission(permission, name, el) {
        return permission ? (
            el
        ) : (
            <Tooltip
              title={el}
              place="right"
              html
            >
                {name}
            </Tooltip>
        );
    }

    render() {
        const { projectId, environmentId } = this.props.match.params;
        const hasNoOperators = !this.props.getValue('segment_operators');
        return (
            <div data-test="segments-page" id="segments-page" className="app-container container">
                <Permission level="project" permission="ADMIN" id={projectId}>
                    {({ permission, isLoading }) => (
                        <SegmentListProvider onSave={this.onSave} onError={this.onError}>
                            {({ isLoading, segments }, { removeSegment }) => (
                                <div className="segments-page">
                                    {isLoading && <div className="centered-container"><Loader/></div>}
                                    {!isLoading && (
                                    <div>
                                        {segments && segments.length ? (
                                            <div>
                                                <Row>
                                                    <Flex>
                                                        <h3>Segments</h3>
                                                        <p>
                                                        Create and manage groups of users with similar traits. Segments can be used to override features within the features page for any environment.
                                                            {' '}
                                                            <ButtonLink target="_blank" href="https://docs.flagsmith.com/basic-features/managing-segments">Learn about Segments.</ButtonLink>
                                                        </p>
                                                    </Flex>
                                                    <FormGroup className="float-right">
                                                        <div className="text-right">
                                                            {permission ? (
                                                                <Button
                                                                  disabled={hasNoOperators}
                                                                  className="btn-lg btn-primary"
                                                                  id="show-create-segment-btn"
                                                                  data-test="show-create-segment-btn"
                                                                  onClick={this.newSegment}
                                                                >
                                                                    Create Segment
                                                                </Button>
                                                            ) : (
                                                                <Tooltip
                                                                  html
                                                                  title={(
                                                                      <Button
                                                                        disabled data-test="show-create-feature-btn" id="show-create-feature-btn"
                                                                        onClick={this.newUser}
                                                                      >
                                                                          Create Segment
                                                                      </Button>
                                                                    )}
                                                                  place="right"
                                                                >
                                                                    {Constants.projectPermissions('Admin')}
                                                                </Tooltip>
                                                            )}
                                                        </div>
                                                    </FormGroup>
                                                </Row>
                                                {hasNoOperators && (
                                                    <div className="mt-2">
                                                        <p className="alert alert-info">
                                                            In order to use segments, please set the segment_operators remote config value. <a target="_blank" href="https://docs.flagsmith.com/deployment/overview#running-flagsmith-on-flagsmith">Learn about self hosting</a>.
                                                        </p>
                                                    </div>
                                                )}

                                                <FormGroup>
                                                    <PanelSearch
                                                      className="no-pad"
                                                      id="segment-list"
                                                      icon="ion-ios-globe"
                                                      title="Segments"
                                                      items={segments}
                                                      renderRow={({ name, id, enabled, description, type }, i) => (
                                                          <Row className="list-item clickable" key={id} space>
                                                              <div
                                                                className="flex flex-1"
                                                                onClick={() => this.editSegment(_.find(segments, { id }), !permission)}
                                                              >
                                                                  <Row>
                                                                      <ButtonLink>
                                                                          <span data-test={`segment-${i}-name`}>
                                                                              {name}
                                                                          </span>
                                                                      </ButtonLink>
                                                                  </Row>
                                                                  <div className="list-item-footer faint">
                                                                      {description || 'No description'}
                                                                  </div>
                                                              </div>
                                                              <Row>
                                                                  <Column>
                                                                      <button
                                                                        disabled={!permission}
                                                                        data-test={`remove-segment-btn-${i}`}
                                                                        onClick={() => this.confirmRemove(_.find(segments, { id }), () => {
                                                                            removeSegment(this.props.match.params.projectId, id);
                                                                        })}
                                                                        className="btn btn--with-icon"
                                                                      >
                                                                          <RemoveIcon/>
                                                                      </button>
                                                                  </Column>
                                                              </Row>
                                                          </Row>
                                                      )}
                                                      renderNoResults={(
                                                          <div className="text-center"/>
                                                    )}
                                                      filterRow={({ name }, search) => name.toLowerCase().indexOf(search) > -1}
                                                    />
                                                </FormGroup>

                                                <div className="mt-2">
                                                    Segments require you to identitfy users, setting traits will add users to segments.
                                                </div>
                                                <FormGroup className="mt-4">
                                                    <CodeHelp
                                                      title="Using segments"
                                                      snippets={Constants.codeHelp.USER_TRAITS(environmentId)}
                                                    />
                                                </FormGroup>
                                            </div>
                                        ) : (
                                            <div>
                                                <h3>Target groups of users with segments.</h3>
                                                <FormGroup>
                                                    <Panel icon="ion-ios-globe" title="1. creating a segment">
                                                        <p>
                                                        You can create a segment that targets
                                                            {' '}
                                                            <ButtonLink
                                                              href="https://docs.flagsmith.com/basic-features/managing-identities#identity-traits"
                                                              target="_blank"
                                                            >User Traits
                                                            </ButtonLink>
                                                        .
                                                        As user's traits are updated they will automatically be added to
                                                        the segments based on the rules you create. <ButtonLink href="https://docs.flagsmith.com/basic-features/managing-segments" target="_blank">Check out the documentation on Segments</ButtonLink>.
                                                        </p>
                                                    </Panel>
                                                </FormGroup>
                                                {this.createSegmentPermission(perm => (
                                                    <FormGroup className="text-center">
                                                        <Button
                                                          disabled={!perm}
                                                          className="btn-lg btn-primary" id="show-create-segment-btn" data-test="show-create-segment-btn"
                                                          onClick={this.newSegment}
                                                        >
                                                            <span className="icon ion-ios-globe"/>
                                                            {' '}
                                                    Create your first Segment
                                                        </Button>
                                                    </FormGroup>
                                                ))}
                                            </div>
                                        )}

                                    </div>
                                    )}
                                    <FormGroup>
                                        <CodeHelp
                                          title="Managing user traits and segments"
                                          snippets={Constants.codeHelp.USER_TRAITS(this.props.match.params.environmentId)}
                                        />
                                    </FormGroup>
                                </div>
                            )}
                        </SegmentListProvider>
                    )}
                </Permission>
            </div>
        );
    }
};

SegmentsPage.propTypes = {};

module.exports = ConfigProvider(SegmentsPage);
