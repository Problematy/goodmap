const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');


module.exports = (env, argv) => {
  const IS_PROD = argv.mode == 'production'

 return {
    devtool: 'source-map',
    entry: "./src/map.js",
    output: {
        path: __dirname + '/dist',
        filename: IS_PROD ? 'map.min.js' : 'map.js',
    },
    resolve: {
        extensions: ['.js', '.jsx', '.css']
    },
    optimization: {
      minimize: IS_PROD,
      minimizer: [
        new TerserPlugin({ parallel: true })
      ]
    },
    module: {
        rules: [
            {
            test: /\.(js|jsx)?/,
                exclude: /node_modules/,
                use: 'babel-loader'
            }
        ]
    }
  }
};
