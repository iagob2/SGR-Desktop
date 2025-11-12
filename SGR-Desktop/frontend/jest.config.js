/**
 * Configuração do Jest para testes do frontend
 */

module.exports = {
    // Ambiente de teste
    testEnvironment: 'jsdom',
    
    // Diretórios onde procurar testes
    roots: ['<rootDir>/tests'],
    
    // Padrão de arquivos de teste
    testMatch: [
        '**/__tests__/**/*.js',
        '**/?(*.)+(spec|test).js'
    ],
    
    // Arquivos a serem ignorados
    testPathIgnorePatterns: [
        '/node_modules/',
        '/dist/'
    ],
    
    // Configuração de cobertura
    collectCoverageFrom: [
        'js/**/*.js',
        '!js/**/*.min.js'
    ],
    
    // Setup files
    setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
    
    // Transformações
    transform: {
        '^.+\\.js$': 'babel-jest'
    },
    
    // Mocks
    moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/$1'
    }
};

