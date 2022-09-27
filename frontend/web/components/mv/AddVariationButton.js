import React from 'react';
import Constants from '../../../common/constants';

export default function AddVariationButton({ onClick, disabled }) {
    return (
        <div className="text-center">
            <button
              disabled={disabled}
              data-test="add-variation" type="button" onClick={onClick}
              className="btn btn--outline "
            >
                Add Variation
            </button>
        </div>
    );
}
