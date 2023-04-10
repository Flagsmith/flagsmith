// Define common loaders for different file types
module.exports = [
    {
        test: /\.m?js$/,
        exclude: /node_modules/,
        use: ['babel-loader'],
    },
    {
        test: /\.tsx?$/,
        exclude: /node_modules/,
        use: ['babel-loader'],
    },

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
