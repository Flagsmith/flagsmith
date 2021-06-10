import React from 'react';
import Constants from '../../../common/constants';

export default function AddVariationButton({ onClick }) {
    return (
        <div className="text-center">
            <Tooltip
              title={(
                  <button type="button" onClick={onClick} className="btn btn--outline ">
                        Add Variation
                  </button>
                )}
              place="right"
            >
                {Constants.strings.MULTIVARIATE_DESCRIPTION}
            </Tooltip>
        </div>
    );
}
