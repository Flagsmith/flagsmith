import React from 'react';
import OriginalLayout from '@theme-original/Layout';
import CrispLoader from './crisp';

export default function Layout(props) {
    return (
        <>
            <CrispLoader />
            <OriginalLayout {...props} />
        </>
    );
}
