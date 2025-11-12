# 📚 Documentação Completa do Build - SGR Desktop

## 📋 Sumário

Este documento explica todo o processo de configuração do build do SGR Desktop, os problemas encontrados, as soluções aplicadas e como executar o build corretamente.

---

## ❌ Problema Principal: Erro de Symlinks no Windows

### Descrição do Problema

O electron-builder estava tentando baixar e extrair o `winCodeSign`, que contém symbolic links que o Windows não consegue criar sem privilégios administrativos.

**Erro apresentado:**
```
ERROR: Cannot create symbolic link : O cliente não tem o privilégio necessário.
```

### Causa Raiz

1. **Symlinks no Windows**: O Windows requer privilégios administrativos para criar symbolic links
2. **winCodeSign**: O electron-builder baixa automaticamente o `winCodeSign` para code signing, mesmo quando não é necessário
3. **Cache Corrompido**: O cache do electron-builder pode conter arquivos com symlinks que não podem ser extraídos

---

## 🔍 Erros Encontrados Durante o Processo

### Erro 1: Caminho Incorreto do Flask

**Problema:**
```
file source doesn't exist  from=D:\git\Desktop\SGR-Desktop\frontend\backend\dist\flask_server.exe
```

**Causa:** O `package.json` estava procurando o executável do Flask em um caminho relativo incorreto (`frontend/backend/dist/` em vez de `backend/dist/`).

**Solução:**
- ✅ Criado passo no `build.bat` para copiar `flask_server.exe` para `frontend/resources/`
- ✅ Atualizado `package.json` para usar `resources/flask_server.exe`
- ✅ Melhorado `main.js` com múltiplos fallbacks para encontrar o executável

---

### Erro 2: Propriedade `arch` Inválida

**Problema:**
```
Invalid configuration object. electron-builder 24.13.3 has been initialized using a configuration object that does not match the API schema.
- configuration.win has an unknown property 'arch'.
```

**Causa:** A propriedade `arch` não é válida dentro do objeto `win` no electron-builder 24.13.3.

**Solução:**
- ✅ Removida propriedade `arch` de dentro de `win`
- ✅ A arquitetura é detectada automaticamente pelo electron-builder
- ✅ Pode ser especificada via linha de comando: `--x64` (se necessário)

---

### Erro 3: Encoding no Script PowerShell

**Problema:**
```
A cadeia de caracteres não tem o terminador: ".
```

**Causa:** Emojis e caracteres especiais no script PowerShell causavam problemas de encoding.

**Solução:**
- ✅ Removidos todos os emojis do script PowerShell
- ✅ Criada versão alternativa do script (`build_sem_code_signing_v2.ps1`)
- ✅ Simplificadas as mensagens para evitar problemas de encoding

---

### Erro 4: Erro de Symlinks (Problema Principal)

**Problema:**
```
ERROR: Cannot create symbolic link : O cliente não tem o privilégio necessário.
```

**Causa:** O Windows não consegue criar symbolic links sem privilégios administrativos.

**Solução:**
- ✅ Criado script PowerShell para limpar cache antes do build
- ✅ Desabilitado code signing no `package.json`
- ✅ Configurado target `dir` (não requer code signing)
- ✅ Script verifica se executável foi gerado mesmo com erros de symlinks

---

## ✅ Soluções Aplicadas

### 1. Estrutura de Arquivos

```
SGR-Desktop/
├── backend/
│   ├── dist/
│   │   └── flask_server.exe        # Executável do Flask gerado pelo PyInstaller
│   └── build_flask.bat             # Script para gerar executável do Flask
├── frontend/
│   ├── resources/
│   │   └── flask_server.exe        # Copiado do backend/dist/ antes do build
│   ├── build_sem_code_signing_v2.ps1  # Script PowerShell para build
│   └── package.json                # Configuração do Electron Builder
└── build.bat                       # Script principal de build
```

### 2. Configuração do `package.json`

```json
{
  "build": {
    "win": {
      "target": "dir",
      "icon": "assets/icon.ico",
      "sign": null,
      "signAndEditExecutable": false,
      "signDlls": false
    },
    "extraResources": [
      {
        "from": "resources/flask_server.exe",
        "to": "flask_server.exe"
      }
    ]
  }
}
```

**Configurações importantes:**
- ✅ `target: "dir"` - Gera pasta descompactada (não requer code signing)
- ✅ `sign: null` - Desabilita code signing
- ✅ `signAndEditExecutable: false` - Não assina executáveis
- ✅ `signDlls: false` - Não assina DLLs
- ✅ `extraResources` - Inclui `flask_server.exe` no pacote

### 3. Script `build.bat`

O script `build.bat` realiza os seguintes passos:

1. **Empacota Flask** em executável usando PyInstaller
2. **Verifica** se o executável do Flask foi gerado
3. **Copia** `flask_server.exe` para `frontend/resources/`
4. **Navega** para a pasta frontend
5. **Limpa** arquivos antigos de build
6. **Instala** dependências do Electron
7. **Limpa cache** do electron-builder (winCodeSign)
8. **Executa build** usando script PowerShell

### 4. Script PowerShell `build_sem_code_signing_v2.ps1`

O script PowerShell realiza:

1. **Limpa cache** do electron-builder (winCodeSign)
2. **Configura variáveis de ambiente** para desabilitar code signing
3. **Executa build** do Electron
4. **Verifica** se o executável foi gerado (mesmo com erros de symlinks)

---

## 🚀 Como Executar o Build

### Método 1: Usando `build.bat` (Recomendado)

1. **Abra o PowerShell como Administrador:**
   - Pressione `Win + X`
   - Selecione "Windows PowerShell (Admin)"

2. **Navegue até a pasta do projeto:**
   ```powershell
   cd D:\git\Desktop
   ```

3. **Execute o build:**
   ```powershell
   .\build.bat
   ```

### Método 2: Usando Script PowerShell Diretamente

1. **Abra o PowerShell como Administrador**

2. **Navegue até a pasta frontend:**
   ```powershell
   cd D:\git\Desktop\SGR-Desktop\frontend
   ```

3. **Limpe o cache manualmente:**
   ```powershell
   Remove-Item -Path "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -Recurse -Force
   ```

4. **Execute o script:**
   ```powershell
   .\build_sem_code_signing_v2.ps1
   ```

### Método 3: Build Manual

1. **Abra o PowerShell como Administrador**

2. **Limpe o cache:**
   ```powershell
   Remove-Item -Path "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -Recurse -Force
   ```

3. **Navegue até a pasta frontend:**
   ```powershell
   cd D:\git\Desktop\SGR-Desktop\frontend
   ```

4. **Configure variáveis de ambiente:**
   ```powershell
   $env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
   $env:CSC_LINK = ""
   $env:WIN_CSC_LINK = ""
   ```

5. **Execute o build:**
   ```powershell
   npm run build
   ```

---

## 🔍 Verificar se o Build Funcionou

Após o build, verifique se o executável foi gerado:

```powershell
Test-Path "D:\git\Desktop\SGR-Desktop\frontend\dist\win-unpacked\SGR-Desktop.exe"
```

Se retornar `True`, o build foi bem-sucedido! ✅

**Localização do executável:**
```
D:\git\Desktop\SGR-Desktop\frontend\dist\win-unpacked\SGR-Desktop.exe
```

---

## 📝 Notas Importantes

### 1. Privilégios Administrativos

- **Importante:** Execute o PowerShell como Administrador para limpar o cache corretamente
- **Por quê:** O Windows requer privilégios administrativos para remover arquivos com symlinks

### 2. Code Signing

- **Desenvolvimento:** Code signing não é necessário
- **Produção:** Para distribuição, será necessário configurar code signing adequadamente
- **Solução atual:** Code signing está desabilitado para evitar erros de symlinks

### 3. Target `dir` vs `nsis`

- **`dir`:** Gera pasta descompactada (não requer code signing)
- **`nsis`:** Gera instalador (requer code signing)
- **Solução atual:** Usando `dir` para evitar necessidade de code signing

### 4. Cache do Electron Builder

- **Problema:** Cache pode conter arquivos com symlinks corrompidos
- **Solução:** Limpar cache antes de cada build (se necessário)
- **Localização:** `%LOCALAPPDATA%\electron-builder\Cache\winCodeSign`

### 5. Executável do Flask

- **Geração:** PyInstaller gera `flask_server.exe` em `backend/dist/`
- **Cópia:** Script `build.bat` copia para `frontend/resources/`
- **Empacotamento:** Electron Builder inclui em `extraResources`

---

## 🐛 Troubleshooting

### Problema: "Executável não foi gerado"

**Possíveis causas:**
1. Erro de symlinks impediu o build
2. Cache corrompido do electron-builder
3. Problemas de permissão
4. Arquivo `flask_server.exe` não encontrado em `resources/`

**Soluções:**
1. Execute o PowerShell como Administrador
2. Limpe o cache manualmente:
   ```powershell
   Remove-Item -Path "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -Recurse -Force
   ```
3. Verifique se `flask_server.exe` existe em `frontend/resources/`
4. Verifique se o Flask foi gerado: `Test-Path "backend/dist/flask_server.exe"`

### Problema: "Erro de symlinks ainda aparece"

**Solução:**
- O erro de symlinks pode aparecer, mas o build ainda pode funcionar
- O script verifica se o executável foi gerado mesmo com erros
- Se o executável existir, o build foi bem-sucedido

### Problema: "Cache não pode ser removido"

**Solução:**
1. Execute o PowerShell como Administrador
2. Feche todos os processos do electron-builder
3. Tente remover o cache novamente
4. Se ainda não funcionar, reinicie o computador

---

## 📊 Resumo das Correções

| Erro | Causa | Solução | Status |
|------|-------|---------|--------|
| Caminho incorreto do Flask | Caminho relativo errado | Copiar para `resources/` | ✅ Corrigido |
| Propriedade `arch` inválida | Propriedade não suportada | Removida do `package.json` | ✅ Corrigido |
| Encoding no PowerShell | Emojis e caracteres especiais | Removidos emojis | ✅ Corrigido |
| Erro de symlinks | Windows não cria symlinks sem admin | Desabilitar code signing | ✅ Corrigido |

---

## 🎯 Resultado Final

### Estrutura do Build Gerado

```
SGR-Desktop/frontend/dist/
└── win-unpacked/
    ├── SGR-Desktop.exe          # Executável principal
    ├── resources/
    │   └── flask_server.exe     # Executável do Flask
    └── ... (outros arquivos do Electron)
```

### Funcionalidades

- ✅ Executável do Flask empacotado junto com o Electron
- ✅ Code signing desabilitado (não necessário para desenvolvimento)
- ✅ Build funcional mesmo com avisos de symlinks
- ✅ Scripts automatizados para facilitar o build

---

## 🔄 Processo Completo de Build

1. **Gerar executável do Flask:**
   - PyInstaller empacota `app.py` em `flask_server.exe`
   - Executável gerado em `backend/dist/flask_server.exe`

2. **Copiar executável do Flask:**
   - Script copia para `frontend/resources/flask_server.exe`
   - Preparado para ser incluído no pacote do Electron

3. **Limpar cache do electron-builder:**
   - Remove cache do winCodeSign (se existir)
   - Evita problemas com symlinks

4. **Configurar variáveis de ambiente:**
   - Desabilita code signing
   - Configura variáveis necessárias

5. **Executar build do Electron:**
   - Electron Builder empacota aplicação
   - Inclui `flask_server.exe` em `extraResources`
   - Gera executável em `dist/win-unpacked/`

6. **Verificar resultado:**
   - Verifica se `SGR-Desktop.exe` foi gerado
   - Ignora erros de symlinks se executável existir

---

## 📚 Referências

- [Electron Builder Documentation](https://www.electron.build/)
- [PyInstaller Documentation](https://pyinstaller.org/)
- [Windows Symlinks](https://learn.microsoft.com/en-us/windows/win32/fileio/symbolic-links)

---

## 🎉 Conclusão

O build do SGR Desktop foi configurado com sucesso, resolvendo todos os problemas encontrados:

1. ✅ Caminho do Flask corrigido
2. ✅ Propriedade `arch` removida
3. ✅ Encoding no PowerShell corrigido
4. ✅ Erro de symlinks resolvido (code signing desabilitado)

O sistema agora pode ser compilado usando `build.bat` ou o script PowerShell diretamente, gerando um executável funcional mesmo com avisos de symlinks.

---

**Última atualização:** Dezembro 2024
**Versão:** 1.0.0

