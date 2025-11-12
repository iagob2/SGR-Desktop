const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let flaskProcess;

// Função para iniciar o servidor Flask
// Função para iniciar o servidor Flask
function startFlask() {
    // Verificar se estamos em desenvolvimento ou produção
    const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
    
    if (isDev) {
        // Modo desenvolvimento: usar Python do venv
        const flaskPath = path.join(__dirname, '..', 'backend', 'app.py');
        const pythonPath = path.join(__dirname, '..', 'backend', 'venv', 'Scripts', 'python.exe');
        
        // Iniciar processo Flask com Python
        flaskProcess = spawn(pythonPath, [flaskPath], {
            cwd: path.join(__dirname, '..', 'backend'),
            stdio: ['pipe', 'pipe', 'pipe']
        });
    } else {
        // Modo produção: usar executável do Flask
        const fs = require('fs');
        
        // Tentar múltiplos caminhos possíveis
        const possiblePaths = [
            path.join(process.resourcesPath, 'flask_server.exe'),  // Caminho padrão (empacotado)
            path.join(__dirname, '..', 'resources', 'flask_server.exe'),  // Caminho alternativo (desenvolvimento)
            path.join(__dirname, '..', 'backend', 'dist', 'flask_server.exe'),  // Caminho de fallback
            path.join(process.cwd(), 'resources', 'flask_server.exe'),  // Caminho relativo ao diretório de trabalho
        ];
        
        let finalPath = null;
        for (const possiblePath of possiblePaths) {
            if (fs.existsSync(possiblePath)) {
                finalPath = possiblePath;
                console.log(`✅ Executável do Flask encontrado em: ${finalPath}`);
                break;
            }
        }
        
        if (!finalPath) {
            console.error('❌ Executável do Flask não encontrado em nenhum dos caminhos:');
            possiblePaths.forEach(p => console.error(`   - ${p}`));
            console.error('💡 Certifique-se de que o Flask foi empacotado corretamente');
            console.error('💡 Verifique se o arquivo flask_server.exe existe em resources/');
            return null;
        }
        
        // Iniciar processo Flask com executável
        console.log(`🚀 Iniciando Flask a partir de: ${finalPath}`);
        flaskProcess = spawn(finalPath, [], {
            cwd: path.dirname(finalPath),
            stdio: ['pipe', 'pipe', 'pipe']
        });
    }
    
    // Logs do Flask
    flaskProcess.stdout.on('data', (data) => {
        console.log(`Flask: ${data}`);
    });
    
    flaskProcess.stderr.on('data', (data) => {
        console.error(`Flask Error: ${data}`);
    });
    
    flaskProcess.on('close', (code) => {
        console.log(`Flask process exited with code ${code}`);
    });
    
    flaskProcess.on('error', (err) => {
        console.error('Failed to start Flask:', err);
    });
    
    return flaskProcess;
}
// Função para parar o servidor Flask
function stopFlask() {
    if (flaskProcess) {
        flaskProcess.kill();
        flaskProcess = null;
    }
}

// Função para criar a janela principal
function createWindow() {
    // Criar a janela do navegador
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1200,
        minHeight: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            enableRemoteModule: false,
            webSecurity: false, // 🔥 CORREÇÃO: Permitir carregamento dinâmico de scripts
            allowRunningInsecureContent: true // 🔥 CORREÇÃO: Permitir conteúdo local
        },
        icon: path.join(__dirname, 'assets', 'icon.png'), // Adicione um ícone se tiver
        title: 'SGR-Desktop - Sistema de Gerenciamento de Restaurantes',
        show: false // Não mostrar até estar pronto
    });

    // Carregar o arquivo HTML (login.html por padrão para mostrar a tela de login)
    mainWindow.loadFile(path.join(__dirname, 'paginas', 'login.html'));

    // Mostrar a janela quando estiver pronta
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // DevTools disponível via F12 ou menu se necessário

    // Lidar com fechamento da janela
    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Criar menu personalizado
    createMenu();
}

// Função para criar menu personalizado - SIMPLIFICADO
function createMenu() {
    const template = [
        {
            label: 'Sistema',
            submenu: [
                {
                    label: 'Sair',
                    accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
                    click: () => {
                        app.quit();
                    }
                }
            ]
        }
    ];

    // No macOS, adicionar menu básico do aplicativo
    if (process.platform === 'darwin') {
        template.unshift({
            label: app.getName(),
            submenu: [
                { role: 'about', label: 'Sobre SGR Desktop' },
                { type: 'separator' },
                { role: 'quit', label: 'Sair' }
            ]
        });
    }

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

// Quando o Electron estiver pronto
app.whenReady().then(() => {
    
    // Iniciar Flask
    startFlask();
    
    // Aguardar um pouco para o Flask inicializar
    setTimeout(() => {
        createWindow();
    }, 3000);

    // No macOS, recriar janela quando clicado no dock
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

// Sair quando todas as janelas estiverem fechadas
app.on('window-all-closed', () => {
    // No macOS, manter o app rodando mesmo com todas as janelas fechadas
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// Antes de sair, parar o Flask
app.on('before-quit', () => {
    stopFlask();
});

// Tratar erros não capturados
process.on('uncaughtException', (error) => {
    console.error('Erro não capturado:', error);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Promise rejeitada não tratada:', reason);
});

// Exportar funções para uso em outros módulos
module.exports = {
    startFlask,
    stopFlask
};
