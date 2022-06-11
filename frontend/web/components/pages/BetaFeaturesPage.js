import React, { Component } from 'react';
import TagValues from '../TagValues';
import Switch from '../Switch';
import EditBetaFeatureModal from '../modals/EditBetaFeature';

const BetaFeaturesPage = class extends Component {
    static displayName = 'BetaFeaturesPage';

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props, context) {
        super(props, context);
        this.state = {
            tags: [],
            showArchived: false,
        };
        ES6Component(this);
    }

    editFeature = (flag, showEnabled, showValue) => {
        openModal('Edit Beta Feature', <EditBetaFeatureModal
          enabled={Utils.getFlagsmithHasFeature(flag)}
          value={Utils.getFlagsmithValue(flag)}
          showEnabled={showEnabled}
          showValue={showValue}
          onSave={(enabled, value) => {
              const toSet = {};
              toSet[`${flag}-opt-in-value`] = value;
              toSet[`${flag}-opt-in-enabled`] = enabled;
              flagsmith.setTraits(toSet).then(() => {
                  location.reload();
              });
          }}
        />);
    }

    resetFeature = (flag) => {
        openConfirm('Please confirm', 'This will reset this feature to use their defaults, are you sure?', () => {
            const toSet = {};
            toSet[`${flag}-opt-in-value`] = null;
            toSet[`${flag}-opt-in-enabled`] = null;
            flagsmith.setTraits(toSet).then(() => {
                location.reload();
            });
        });
    }

    render() {
        let features = {};
        try {
            features = JSON.parse(Utils.getFlagsmithValue('beta_features'));
        } catch (e) {
            return <div><Loader/></div>;
        }
        return (
            <div
              data-test="beta-features-page"
              id="beta-features-page"
              className="app-container container-fluid"
            >
                <h3>Beta Features</h3>
                <p>
                    The Flagsmith web application uses Flagsmith to manage all of its features. To demonstrate this, here you can manage features for your user!
                </p>
                {
                    Object.keys(features).map((v) => {
                        const featureCategory = features[v];
                        return (
                            <div className="mb-4">
                                <h4 className="mb-4">
                                    {Format.camelCase(v)}
                                </h4>
                                <div className="mt-2 mb-2">
                                    {!featureCategory.length && <div>There are no features in this category right now.</div>}
                                    {!!featureCategory.length && (
                                        <PanelSearch
                                          className="no-pad"
                                          id="features-list"
                                          icon="ion-ios-rocket"
                                          title="Features"
                                          renderSearchWithNoResults
                                          items={features[v]}
                                          renderRow={feature => (
                                              <div onClick={() => this.editFeature(feature.flag, feature.hasEnabled, feature.hasValue)} className="list-item clickable">
                                                  <Row>
                                                      <Flex>
                                                          <div>
                                                              <strong>
                                                                  {feature.flag}
                                                              </strong>
                                                          </div>
                                                          <div className="list-item-footer faint">
                                                              {feature.description}
                                                          </div>
                                                      </Flex>
                                                      {feature.hasValue && (
                                                          <div className="mr-2">
                                                              <FeatureValue value={Utils.getFlagsmithValue(feature.flag)}/>
                                                          </div>
                                                      )}
                                                      {feature.hasEnabled && (
                                                          <div className="mr-2">
                                                              <Switch checked={Utils.getFlagsmithHasFeature(feature.flag)}/>
                                                          </div>
                                                      )}
                                                      {
                                                          typeof flagsmith.getTrait(`${feature.flag}-opt-in-enabled`) === 'boolean' && (
                                                              <Button onClick={(e) => {
                                                                  e.preventDefault();
                                                                  e.stopPropagation();

                                                                  this.resetFeature(feature.flag);
                                                              }}
                                                              >
                                                                  Reset
                                                              </Button>
                                                          )
                                                      }
                                                  </Row>

                                              </div>
                                          )}
                                          itemHeight={65}
                                        />
                                    )}

                                </div>
                            </div>
                        );
                    })
                }
            </div>

        );
    }
};

BetaFeaturesPage.propTypes = {};

module.exports = hot(module)(ConfigProvider(BetaFeaturesPage));
