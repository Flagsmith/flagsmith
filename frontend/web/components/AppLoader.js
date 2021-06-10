import React from 'react';

export default function AppLoader() {
    return (
        <div style={{
            position: 'absolute',
            top: '35%',
            width: '100%',
            textAlign: 'center',
        }}
        >
            <Loader />
        </div>
    );
}
