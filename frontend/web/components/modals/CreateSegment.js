import React, { Component, useEffect, useState } from 'react';
import engine from 'bullet-train-rules-engine';
import Rule from './Rule';
import SegmentStore from '../../../common/stores/segment-list-store';
import IdentityListProvider from '../../../common/providers/IdentityListProvider';
import Constants from '../../../common/constants';
import EnvironmentSelect from '../EnvironmentSelect';
import Tabs from '../base/forms/Tabs';
import TabItem from '../base/forms/TabItem';
import AssociatedSegmentOverrides from './AssociatedSegmentOverrides';
import InfoMessage from '../InfoMessage';
import _data from "../../../common/data/base/_data";
import JSONReference from "../JSONReference";

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
            environmentId: props.environmentId,
            id,
            isValid: this.validateRules(rules),
            data: '{\n}',
        };

        AppActions.getIdentities(props.environmentId);

        this.listenTo(SegmentStore, 'saved', (segment) => {
            if (this.props.onComplete) {
                this.props.onComplete(segment);
            } else {
                this.close();
            }
        });
        this.listenTo(SegmentStore, 'problem', () => {
            this.setState({ error: true });
        });
    }

    validateRules = (rules) => {
        if (!rules || !rules[0] || !rules[0].rules) {
            return false;
        }
        const res = rules[0].rules.find(v => v.conditions.find(c => !Utils.validateRule(c)));

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
            this.input?.focus?.();
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
                AppActions.editSegment(this.props.projectId, { description, name, rules, id: this.props.segment.id, feature: this.props.feature });
            } else {
                AppActions.createSegment(this.props.projectId, { description, name, rules, feature: this.props.feature });
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
            <div className="overflow-visible">
                <div>
                    <div className="mb-2">
                        {rules[0].rules.map((rule, i) => (
                            <div key={i}>
                                {i > 0 && (
                                    <Row className="and-divider my-1">
                                        <Flex className="and-divider__line"/>
                                        {rule.type === 'ANY' ? 'AND' : 'AND NOT'}
                                        <Flex className="and-divider__line"/>
                                    </Row>
                                )}
                                <Rule
                                  showDescription={this.state.showDescriptions}
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
                    </div>
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
                {!this.props.condensed && (
                    <div className="mt-4">
                        <InfoMessage>
                            Learn more about rule and trait value type conversions <a href="https://docs-git-improvement-segment-rule-value-typing-flagsmith.vercel.app/basic-features/managing-segments#rule-typing">here</a>.
                        </InfoMessage>
                    </div>
                )}

                {!isEdit && (
                    <Row className="mb-4">
                        <label className="mr-2 mb-0" htmlFor="segmentID">
                            ID
                        </label>
                        <Flex>
                            <Input
                              ref={e => this.input = e}
                              data-test="segmentID"
                              name="id"
                              id="segmentID"
                              readOnly={isEdit}
                              maxLength={SEGMENT_ID_MAXLENGTH}
                              value={name}
                              onChange={e => this.setState({ name: Format.enumeration.set(Utils.safeParseEventValue(e)).toLowerCase() })}
                              isValid={name && name.length}
                              type="text" title={isEdit ? 'ID' : 'ID*'}
                              placeholder="E.g. power_users"
                            />
                        </Flex>

                    </Row>
                )}


                {!this.props.condensed && (
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
                )}


                <div className="form-group ">
                    <Row className="mt-2 mb-2">
                        <Flex>
                            <label className="cols-sm-2 control-label">Include users when the following rules apply:</label>
                            <span className="text-small text-muted">Note: Trait names are case sensitive</span>
                        </Flex>
                        <span>
                            {this.state.showDescriptions? "Hide condition descriptions" : "Show condition descriptions"}
                        </span>
                        <Switch checked={!!this.state.showDescriptions} onChange={()=>{this.setState({showDescriptions:!this.state.showDescriptions})}}/>
                    </Row>
                    {
                        rulesEl
                    }
                </div>
                {error
                    && <div className="alert alert-danger">Error creating segment, please ensure you have entered a trait and value for each rule.</div>
                }
                {isEdit && (
                    <JSONReference title={"Segment"} json={this.props.segment}/>
                )}
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
                        <Row className="justify-content-end">
                            {this.props.condensed && (
                                <ButtonLink type="button" onClick={this.props.onCancel} className="mr-4">Cancel</ButtonLink>
                            )}
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
                        </Row>

                    </div>
                )}

            </form>
        );

        const { environmentId } = this.state;

        return (
            <div>
                {isEdit && !this.props.condensed ? (
                    <Tabs value={this.state.tab} onChange={tab => this.setState({ tab })}>
                        <TabItem tabLabel="Rules">
                            <div className="mt-4 mr-3 ml-3">
                                {Tab1}
                            </div>
                        </TabItem>
                        {this.props.hasFeature('segment_associated_features') && (
                            <TabItem tabLabel="Features">
                                <div className="mt-4 mr-3 ml-3">
                                    <AssociatedSegmentOverrides feature={this.props.segment.feature} projectId={this.props.projectId} id={this.props.segment.id}/>
                                </div>
                            </TabItem>
                        )}

                        <TabItem tabLabel="Users">
                            <div className="mt-4 mr-3 ml-3">
                                <InfoMessage>
                                    This is a random sample of Identities who are either in or out of this Segment based on the current Segment rules.
                                </InfoMessage>
                                <IdentityListProvider>
                                    {({ isLoading, identities, identitiesPaging }) => (
                                        <div className="mt-2">
                                            <FormGroup>

                                                <InputGroup
                                                  title="Environment"
                                                  component={(
                                                      <EnvironmentSelect
                                                        value={this.state.environmentId}
                                                        onChange={(environmentId) => {
                                                            this.setState({ environmentId });
                                                            AppActions.getIdentities(environmentId);
                                                        }}
                                                      />
)}
                                                />
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
                                                      AppActions.searchIdentities(this.state.environmentId, Utils.safeParseEventValue(e));
                                                  }}
                                                />
                                            </FormGroup>
                                        </div>
                                    )}
                                </IdentityListProvider>
                            </div>
                        </TabItem>
                    </Tabs>
                ) :<div className="mt-4 mr-3 ml-3">{Tab1}</div>}
            </div>
        );
    }
};
CreateSegment.propTypes = {};



const LoadingCreateSegment  = (props) => {
    const [loading, setLoading] = useState(!!props.segment);
    const [segmentData, setSegmentData] = useState(null);

    useEffect(()=>{
        if(props.segment) {
            _data.get(`${Project.api}projects/${props.projectId}/segments/${props.segment}`).then((segment)=> {
                setSegmentData(segment);
                setLoading(false)
            })
        }
    },[props.segment])

    return loading?<div className="text-center"><Loader/></div> : (
        <CreateSegment {...props} segment={segmentData}/>
    )
}

export default LoadingCreateSegment

module.exports = hot(module)(ConfigProvider(LoadingCreateSegment));
