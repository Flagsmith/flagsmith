// Define common loaders for different file types
module.exports = [
  {
    exclude: /node_modules/,
    test: /\.m?js$/,
    use: ['babel-loader'],
  },
  {
    exclude: /node_modules/,
    test: /\.tsx?$/,
    use: ['babel-loader'],
  },
  { exclude: /node_modules/, loader: 'json-loader', test: /.json$/ },

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
]
