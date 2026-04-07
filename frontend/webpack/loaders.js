// Define common loaders for different file types
module.exports = [
    {
        test: /\.m?js$/,
        exclude: /node_modules/,
        use: ['babel-loader'],
    },
    {
        // Allow ESM modules from node_modules (e.g. remark-gfm, unified)
        test: /\.m?js$/,
        include: /node_modules/,
        resolve: { fullySpecified: false },
        type: 'javascript/auto',
    },
    {
        test: /\.tsx?$/,
        exclude: /node_modules/,
        use: ['babel-loader'],
    },
    { test: /.json$/, loader: 'json-loader', exclude: /node_modules/ },

    {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
    },
    {
        test: /\.(md|txt)$/,
        use: 'raw-loader',
    },
    {
        test: /\.html$/,
        use: 'html-loader',
    },
    {
        test: /\.(otf|ttf|eot|png|jpg|jpeg|gif|svg|woff|woff2|ogv|mp4|webm)$/,
        use: 'file-loader?hash=sha512&digest=hex&name=[hash].[ext]',
    },
];
