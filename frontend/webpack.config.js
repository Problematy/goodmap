const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = (env, argv) => {
    const IS_PROD = argv.mode === 'production';
    const runOnAllInterfaces = env && env.serve === 'network';

    return {
        devtool: 'source-map',
        entry: './src/index.js',
        output: {
            path: `${__dirname}/dist`,
            filename: IS_PROD ? 'index.min.js' : 'index.js',
        },
        resolve: {
            extensions: ['.js', '.jsx', '.css'],
        },
        optimization: {
            minimize: IS_PROD,
            minimizer: [new TerserPlugin({ parallel: true })],
        },
        module: {
            rules: [
                {
                    test: /\.(js|jsx)?/,
                    loader: 'babel-loader',
                    exclude: /node_modules/,
                },
                {
                    test: /\.css$/,
                    use: ['style-loader', 'css-loader'], // Use both style-loader and css-loader
                },
                {
                    test: /\.(jpe?g|png|gif|woff|woff2|eot|ttf|svg)(\?[a-z0-9=.]+)?$/,
                    loader: 'url-loader',
                },
            ],
        },
        devServer: {
            host: runOnAllInterfaces ? '0.0.0.0' : 'localhost',
            port: 8080,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
                'Access-Control-Allow-Headers': 'X-Requested-With, content-type, Authorization'
            },
            allowedHosts: runOnAllInterfaces ? 'all' : 'localhost',
        },
    };

};
