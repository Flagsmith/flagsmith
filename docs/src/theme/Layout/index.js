import React from 'react';
import OriginalLayout from '@theme-original/Layout';
import CrispLoader from './crisp';  // adjust path if you moved it

export default function Layout(props) {
    return (
        <>
            <CrispLoader />
            <OriginalLayout {...props} />
        </>
    );
}
