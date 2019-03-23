const webpack = require('webpack');
const path = require('path');

module.exports = {
  entry: './src/index.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js'
  },
  optimization: {
      minimize: false
  },
  devServer: {
    contentBase: __dirname,
    compress: false,
    port: 8080
  }
};