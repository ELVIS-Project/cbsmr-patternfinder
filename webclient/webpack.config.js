const webpack = require('webpack');
const path = require('path');

module.exports = {
	entry: __dirname + '/src/search.js',
	output: {
		path: path.resolve(__dirname, 'dist'),
		filename: 'search.js'
	},
	module: {
		rules: [{
			test: /\.css$/,
			use: ['style-loader', 'css-loader']
		}]
	},
	devServer: {
		contentBase: __dirname,
		compress: false,
		port: 8080,
		headers: {
			'Access-Control-Allow-Origin': '*',
			'Access-Control-Allow-Headers': '*'
		}

	}
};
