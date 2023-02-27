const path = require('path');

module.exports = {
    resolve: {
        extensions: ['.tsx', '.ts', '.js'],
        alias: {
            'common': path.resolve(__dirname, 'common'),
        },
    },
    externals: {
        'jquery': 'jQuery',
    },
};
