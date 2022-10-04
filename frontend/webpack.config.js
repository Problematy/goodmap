const webpack = require('webpack');
module.exports = {
    devtool: 'source-map',
    entry:  './src/map.js',
    output: {
        path: __dirname + '/dist',
        filename: 'map.js',
    },
    resolve: {
        extensions: ['.js', '.jsx', '.css']
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
};
