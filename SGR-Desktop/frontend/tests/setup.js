/**
 * Setup global para testes Jest
 * 
 * Configurações e mocks globais que são aplicados a todos os testes
 */

// Mock do localStorage
const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
};

global.localStorage = localStorageMock;

// Mock do window.location
delete window.location;
window.location = {
    href: '',
    assign: jest.fn(),
    replace: jest.fn(),
    reload: jest.fn(),
};

// Mock do console para evitar poluição nos testes
global.console = {
    ...console,
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    info: jest.fn(),
};

