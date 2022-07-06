import React from 'react';
import Constants from '../../../common/constants';
import VariationValue from './VariationValue';
import ValueEditor from '../ValueEditor';
import InfoMessage from '../InfoMessage';

export default function VariationOptions({ multivariateOptions, select, controlValue, weightTitle, variationOverrides, removeVariation, updateVariation, setVariations, setValue, preventRemove }) {
    const invalid = multivariateOptions.length && controlValue < 0;

    if (!multivariateOptions || !multivariateOptions.length) {
        return null;
    }
    const controlSelected = !variationOverrides || !variationOverrides.find(v => v.percentage_allocation === 100);
    return (
        <>
            {invalid && (
                <div className="alert alert-danger">
                    Your variation percentage splits total to over 100%
                </div>
            )}
            {!preventRemove && (
                <p>
                    <InfoMessage>
                        Variation values are shared amongst environments. Variation weights are specific to this Environment. <a target="_blank" href="https://docs.flagsmith.com/basic-features/managing-features#multi-variate-flags">Check the Docs for more</a>
                    </InfoMessage>
                </p>
            )}

            {select && (
                <div className="panel panel--flat panel-without-heading mb-2">
                    <div className="panel-content">
                        <Row>
                            <Flex>
                                <ValueEditor value={Utils.getTypedValue(controlValue)}/>
                            </Flex>
                            <div
                              onMouseDown={(e) => {
                                  e.stopPropagation();
                                  setVariations([]);
                                  setValue(controlValue);
                              }}
                              className={`btn--radio ion ${controlSelected ? 'ion-ios-radio-button-on' : 'ion-ios-radio-button-off'}`}
                            />
                        </Row>
                    </div>
                </div>
            )}
            {
                multivariateOptions.map((theValue, i) => {
                    const override = select
                        ? variationOverrides && variationOverrides[0] && typeof variationOverrides[0].multivariate_feature_option_index === 'number' ? i === variationOverrides[0].multivariate_feature_option_index
&& variationOverrides[0] : variationOverrides && variationOverrides.find(v => v.multivariate_feature_option === theValue.id) : variationOverrides && variationOverrides.find(v => v.percentage_allocation === 100);
                    return select ? (
                        <div className="panel panel--flat panel-without-heading mb-2">
                            <div className="panel-content">
                                <Row>
                                    <Flex>
                                        <ValueEditor value={Utils.getTypedValue(Utils.featureStateToValue(theValue))}/>
                                    </Flex>
                                    <div
                                        data-test={`select-variation-${i+1}`}
                                        onMouseDown={(e) => {
                                          e.stopPropagation();
                                          e.preventDefault();
                                          setVariations([{
                                              multivariate_feature_option: theValue.id,
                                              multivariate_feature_option_index: i,
                                              percentage_allocation: 100,
                                          }]);
                                          return false;
                                      }}
                                      className={`btn--radio ion ${override ? 'ion-ios-radio-button-on' : 'ion-ios-radio-button-off'}`}
                                    />
                                </Row>
                            </div>
                        </div>
                    ) : (
                        <VariationValue
                          key={i}
                          index={i}
                          preventRemove={preventRemove}
                          value={theValue}
                          onChange={(e) => {
                              updateVariation(i, e, variationOverrides);
                          }}
                          weightTitle={weightTitle}
                          onRemove={preventRemove ? null : () => removeVariation(i)}
                        />
                    );
                })
            }
        </>
    );
}
