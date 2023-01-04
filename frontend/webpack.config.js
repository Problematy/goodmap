const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = (env, argv) => {
    const IS_PROD = argv.mode === 'production';

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
                    exclude: /node_modules/,
                    use: 'babel-loader',
                },
            ],
        },
    };
};
