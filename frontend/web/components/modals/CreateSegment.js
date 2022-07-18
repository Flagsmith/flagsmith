import React, { Component } from 'react';
import engine from 'bullet-train-rules-engine';
import { Tab } from '@material-ui/core';
import Rule from './Rule';
import Highlight from '../Highlight';
import SegmentStore from '../../../common/stores/segment-list-store';
import IdentityListProvider from '../../../common/providers/IdentityListProvider';
import Constants from '../../../common/constants';
import Tabs from '../base/forms/Tabs';
import TabItem from '../base/forms/TabItem';
import AssociatedSegmentOverrides from './AssociatedSegmentOverrides';

const SEGMENT_ID_MAXLENGTH = Constants.forms.maxLength.SEGMENT_ID;

const CreateSegment = class extends Component {
    static displayName = 'CreateSegment'

    constructor(props, context) {
        super(props, context);
        ES6Component(this, this.onUnmount);
        const { description, name, id, rules = [] } = this.props.segment && this.props.segment.rules.length ? _.cloneDeep(this.props.segment)
            : {
                rules: [{
                    type: 'ALL',
                    rules: [
                        {
                            type: 'ANY',
                            conditions: [
                                { ...Constants.defaultRule },
                            ],
                        },
                    ],
                }],
            };

        this.state = {
            tab: 0,
            description,
            name,
            rules,
            id,
            isValid: this.validateRules(rules),
            data: '{\n}',
        };
        AppActions.getIdentities(props.environmentId);

        this.listenTo(SegmentStore, 'saved', () => {
            this.close();
        });
        this.listenTo(SegmentStore, 'problem', () => {
            this.setState({ error: true });
        });
    }

    validateRules = (rules) => {
        if (!rules || !rules[0] || !rules[0].rules) {
            return false;
        }
        const res = rules[0].rules.find(v => v.conditions.find(c => {
            return !Utils.validateRule(c);
        }));

        return !res;
    }

    addRule = (type = 'ANY') => {
        const rules = this.state.rules;
        rules[0].rules = rules[0].rules.concat({
            type,
            conditions: [
                { ...Constants.defaultRule },
            ],
        });
        this.setState({ rules, isValid: this.validateRules(rules) });
    }

    updateRule = (rulesIndex, elementNumber, newValue) => {
        const { rules } = this.state;
        rules[0].rules[elementNumber] = newValue;
        this.setData(this.state.exampleData);
        this.setState({ rules, isValid: this.validateRules(rules) });
    }

    removeRule = (rulesIndex, elementNumber) => {
        const { rules } = this.state;
        rules[0].rules.splice(elementNumber, 1);
        this.setData(this.state.exampleData);
        this.setState({ rules });
    }

    close() {
        closeModal();
    }


    componentDidMount = () => {
        this.focusTimeout = setTimeout(() => {
            this.input.focus();
            this.focusTimeout = null;
        }, 500);
    };

    onUnmount() {
        if (this.focusTimeout) {
            clearTimeout(this.focusTimeout);
        }
    }


    save = (e) => {
        Utils.preventDefault(e);
        const { state: { description = '', id, name, rules } } = this;
        if (name) {
            if (this.props.segment) {
                AppActions.editSegment(this.props.projectId, { description, name, rules, id: this.props.segment.id });
            } else {
                AppActions.createSegment(this.props.projectId, { description, name, rules });
            }
        }
    };

    setData = (data) => {
        try {
            data = JSON.parse(data);
            engine(data, this.state.rules)
                .then((ruleEval) => {
                    this.setState({ exampleData: data, ruleEval });
                });
        } catch (e) {
        }

        // this.codeEditor.highlightCode();
        // this.setState({data})
    }

    render() {
        const { name, description, rules, isSaving, error } = this.state;
        const { isEdit, identity, readOnly } = this.props;

        const rulesEl = (
            <div className="panel--grey overflow-visible">
                <div>
                    <FormGroup>
                        {rules[0].rules.map((rule, i) => (
                            <div key={i}>
                                {i > 0 && (
                                    <Row className="and-divider">
                                        <Flex className="and-divider__line"/>
                                        {rule.type === 'ANY' ? 'AND' : 'AND NOT'}
                                        <Flex className="and-divider__line"/>
                                    </Row>
                                )}
                                <Rule
                                  readOnly={readOnly}
                                  data-test={`rule-${i}`}
                                  rule={rule}
                                  operators={
                                      Utils.getFlagsmithValue('segment_operators') ? JSON.parse(Utils.getFlagsmithValue('segment_operators')) : null
                                  }
                                  onRemove={v => this.removeRule(0, i, v)}
                                  onChange={v => this.updateRule(0, i, v)}
                                />
                            </div>
                        ))}
                    </FormGroup>
                    <Row className="justify-content-center">
                        {!readOnly && (
                        <div
                          onClick={() => this.addRule('ANY')} style={{ marginTop: 20 }}
                          className="text-center"
                        >
                            <ButtonOutline data-test="add-rule" type="button">
                              Add AND Condition
                            </ButtonOutline>
                        </div>
                        )}
                        {!readOnly && Utils.getFlagsmithHasFeature('not_operator') && (
                            <div
                              onClick={() => this.addRule('NOT')} style={{ marginTop: 20 }}
                              className="text-center"
                            >
                                {
                                    Utils.getFlagsmithValue('not_operator') ? (
                                        <Tooltip title={(
                                            <ButtonOutline className="ml-2 btn--outline-danger" data-test="add-rule" type="button">
                                                Add AND NOT Condition
                                            </ButtonOutline>
                                        )}
                                        >
                                            {`Note: If using clientside evaluations on your SDK, this feature is only supported by the following SDKs: ${JSON.parse(Utils.getFlagsmithValue('not_operator'))}`}
                                        </Tooltip>
                                    ) : (
                                        <ButtonOutline className="ml-2 btn--outline-danger" data-test="add-rule" type="button">
                                            Add AND NOT Condition
                                        </ButtonOutline>
                                    )
                                }
                            </div>
                        )}
                    </Row>
                </div>
            </div>
        );


        const Tab1 = (
            <form
              id="create-segment-modal"
              onSubmit={this.save}
            >
                <FormGroup className="mb-4">
                    <InputGroup
                      ref={e => this.input = e}
                      data-test="segmentID"
                      inputProps={{
                          className: 'full-width',
                          name: 'segmentID',
                          readOnly: isEdit,
                          maxLength: SEGMENT_ID_MAXLENGTH,
                      }}
                      value={name}
                      onChange={e => this.setState({ name: Format.enumeration.set(Utils.safeParseEventValue(e)).toLowerCase() })}
                      isValid={name && name.length}
                      type="text" title={isEdit ? 'ID' : 'ID*'}
                      placeholder="E.g. power_users"
                    />
                </FormGroup>

                <FormGroup className="mb-4">
                    <InputGroup
                      value={description}
                      inputProps={{
                          className: 'full-width',
                          readOnly: !!identity || readOnly,
                          name: 'featureDesc',
                      }}
                      onChange={e => this.setState({ description: Utils.safeParseEventValue(e) })}
                      isValid={name && name.length}
                      type="text" title="Description (optional)"
                      placeholder="e.g. 'People who have spent over $100' "
                    />
                </FormGroup>

                <div className="form-group ">
                    <label className="cols-sm-2 control-label">Include users when</label>
                    <p>Trait names are case sensitive</p>
                    {
                    rulesEl
                }
                </div>

                {error
                && <div className="alert alert-danger">Error creating segment, please ensure you have entered a trait and value for each rule.</div>
            }

                {this.props.readOnly ? (
                    <div className="text-right">
                        <Tooltip
                          html
                          title={(
                              <Button
                                disabled data-test="show-create-feature-btn" id="show-create-feature-btn"
                              >
                                Update Segment
                              </Button>
                        )}
                          place="left"
                        >
                            {Constants.projectPermissions('Admin')}
                        </Tooltip>
                    </div>
                ) : (
                    <div className="text-right">
                        {isEdit ? (
                            <Button
                              type="submit" data-test="update-segment" id="update-feature-btn"
                              disabled={isSaving || !name || !this.state.isValid}
                            >
                                {isSaving ? 'Creating' : 'Update Segment'}
                            </Button>
                        ) : (
                            <Button
                              type="submit" data-test="create-segment" disabled
                              id="create-feature-btn"
                              disabled={isSaving || !name || !this.state.isValid}
                            >
                                {isSaving ? 'Creating' : 'Create Segment'}
                            </Button>
                        )}
                    </div>
                )}

            </form>
        );

        const { environmentId } = this.props;

        return (
            <div className="mt-2 mr-3 ml-3">
                {isEdit ? (
                    <Tabs value={this.state.tab} onChange={tab => this.setState({ tab })}>
                        <TabItem tabLabel="Rules">
                            <div className="mt-2">
                                {Tab1}
                            </div>
                        </TabItem>
                        <TabItem tabLabel="Features">
                            <AssociatedSegmentOverrides projectId={this.props.projectId} id={this.props.segment.id}/>
                        </TabItem>
                        <TabItem tabLabel="Users">
                            <div className="mt-2">
                                <IdentityListProvider>
                                    {({ isLoading, identities, identitiesPaging }) => (
                                        <div className="mt-2">
                                            <FormGroup>
                                                <PanelSearch
                                                  renderSearchWithNoResults
                                                  id="users-list"
                                                  title="Segment Users"
                                                  className="no-pad"
                                                  isLoading={isLoading}
                                                  icon="ion-md-person"
                                                  items={identities}
                                                  paging={identitiesPaging}
                                                  showExactFilter
                                                  nextPage={() => AppActions.getIdentitiesPage(environmentId, identitiesPaging.next)}
                                                  prevPage={() => AppActions.getIdentitiesPage(environmentId, identitiesPaging.previous)}
                                                  goToPage={page => AppActions.getIdentitiesPage(environmentId, `${Project.api}environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/?page=${page}`)}
                                                  renderRow={({
                                                      id,
                                                      identifier,
                                                  }, index) => (
                                                      <div key={id}>
                                                          <IdentitySegmentsProvider fetch id={id} projectId={this.props.projectId}>{({ isLoading: segmentsLoading, segments }) => {
                                                              let inSegment = false;
                                                              if (segments && segments.find(v => v.name === name)) {
                                                                  inSegment = true;
                                                              }
                                                              return (
                                                                  <Row
                                                                    space className="list-item clickable" key={id}
                                                                    data-test={`user-item-${index}`}
                                                                  >
                                                                      <strong>
                                                                          {identifier}
                                                                      </strong>
                                                                      <div className={`${inSegment ? 'strong text-primary' : 'text-faint muted faint text-small'} badge`}>
                                                                          <span className={`ion mr-1 line ${inSegment ? ' text-primary ion-ios-checkmark-circle' : 'ion-ios-remove-circle'}`}/>
                                                                          {inSegment ? 'User in segment' : 'Not in segment'}
                                                                      </div>
                                                                  </Row>
                                                              );
                                                          }}
                                                          </IdentitySegmentsProvider>
                                                      </div>
                                                  )}
                                                  filterRow={(flag, search) => flag.identifier && flag.identifier.toLowerCase().indexOf(search) !== -1}
                                                  search={this.state.search}
                                                  onChange={(e) => {
                                                      this.setState({ search: Utils.safeParseEventValue(e) });
                                                      AppActions.searchIdentities(this.props.environmentId, Utils.safeParseEventValue(e));
                                                  }}
                                                />
                                                <p className="text-right mt-4">This is a random sample of users who are either in or out of the Segment.</p>
                                            </FormGroup>
                                        </div>
                                    )}
                                </IdentityListProvider>
                            </div>
                        </TabItem>
                    </Tabs>
                ) : Tab1}
            </div>
        );
    }
};
CreateSegment.propTypes = {};

module.exports = hot(module)(ConfigProvider(CreateSegment));
