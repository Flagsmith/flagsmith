import React from 'react';
import Constants from '../../../common/constants';
import VariationValue from './VariationValue';

export default function VariationOptions({ multivariateOptions, select, controlValue, weightTitle, variationOverrides, removeVariation, updateVariation, setVariations, setValue }) {
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
            <Tooltip
              title={(
                  <label>{select ? 'Value' : 'Variations'} <span className="icon ion-ios-information-circle"/></label>
                )}
              html
              place="right"
            >
                {Constants.strings.MULTIVARIATE_DESCRIPTION}
            </Tooltip>
            {select && (
                <div className="panel panel--flat panel-without-heading mb-2">
                    <div className="panel-content">
                        <Row>
                            <div className="flex flex-1 align-start">
                                <FeatureValue value={Utils.getTypedValue(controlValue)}/>
                            </div>
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
                multivariateOptions.map((m, i) => {
                    const theValue = {
                        ...m,
                        ...(override ? { default_percentage_allocation: override.percentage_allocation } : {}),
                    };
                    let override = select
                        ? variationOverrides && variationOverrides[0] && typeof variationOverrides[0].multivariate_feature_option_index === 'number' ? i === variationOverrides[0].multivariate_feature_option_index
&& variationOverrides[0] : variationOverrides && variationOverrides.find(v => v.multivariate_feature_option === m.id) : variationOverrides && variationOverrides.find(v => v.percentage_allocation === 100);
                    return select ? (
                        <div className="panel panel--flat panel-without-heading mb-2">
                            <div className="panel-content">
                                <Row>
                                    <div className="flex flex-1 align-start">
                                        <FeatureValue value={Utils.getTypedValue(Utils.featureStateToValue(theValue))}/>
                                    </div>
                                    <div
                                      onMouseDown={(e) => {
                                          e.stopPropagation();
                                          e.preventDefault();
                                          setVariations([{
                                              multivariate_feature_option: m.id,
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
                          value={theValue}
                          onChange={(e) => {
                              updateVariation(i, e, variationOverrides);
                          }}
                          weightTitle={weightTitle}
                          onRemove={() => removeVariation(i)}
                        />
                    );
                })
            }
        </>
    );
}
