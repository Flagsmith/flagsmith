import React from 'react';
import Constants from '../../../common/constants';

export default function AddVariationButton({ onClick }) {
    return (
        <div className="text-center">
            <button type="button" onClick={onClick} className="btn btn--outline ">
                Add Variation
            </button>
        </div>
    );
}
