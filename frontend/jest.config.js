module.exports = {
    setupFiles: ['<rootDir>/src/i18n'],
    verbose: true,
    testEnvironment: 'jsdom',
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
    collectCoverageFrom: ['src/components/**/*.jsx'],
    coverageThreshold: {
        global: {
            statements: 75,
            branches: 60,
            functions: 70,
            lines: 75,
        },
    },
    transform: {
        '^.+\\.(js|jsx)$': 'babel-jest',
    },
    transformIgnorePatterns: [
        'node_modules/(?!(react-leaflet|@react-leaflet/core|react-leaflet-custom-control|react-leaflet-cluster|uuid)/)',
    ],
    moduleNameMapper: {
        '\\.(css|less)$': '<rootDir>/__mocks__/styleMock.js',
        '\\.(png|jpg|jpeg|gif|svg)$': '<rootDir>/__mocks__/fileMock.js',
    },
};
