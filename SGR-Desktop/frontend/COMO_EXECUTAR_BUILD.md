# Como Executar o Build - Guia Passo a Passo

## Problema: Erro de Symlinks

O electron-builder está tentando baixar o `winCodeSign`, que contém symbolic links que o Windows não consegue criar sem privilégios administrativos.

## Solução Definitiva (Passo a Passo)

### Opção 1: Limpar Cache Manualmente (MAIS EFICAZ)

1. **Abra o PowerShell como Administrador:**
   - Pressione `Win + X`
   - Selecione "Windows PowerShell (Admin)" ou "Terminal (Admin)"
   - Ou clique com botão direito no PowerShell e selecione "Executar como administrador"

2. **Limpe o cache do electron-builder:**
   ```powershell
   Remove-Item -Path "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -Recurse -Force
   ```

3. **Navegue até a pasta do projeto:**
   ```powershell
   cd D:\git\Desktop
   ```

4. **Execute o build:**
   ```powershell
   .\build.bat
   ```

### Opção 2: Usar Script PowerShell

1. **Abra o PowerShell como Administrador** (importante!)

2. **Navegue até a pasta frontend:**
   ```powershell
   cd D:\git\Desktop\SGR-Desktop\frontend
   ```

3. **Execute o script:**
   ```powershell
   .\build_sem_code_signing.ps1
   ```

   **OU use a versão alternativa:**
   ```powershell
   .\build_sem_code_signing_v2.ps1
   ```

### Opção 3: Build Manual (Se scripts não funcionarem)

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

## Verificar se Funcionou

Após o build, verifique se o executável foi gerado:

```powershell
Test-Path "dist\win-unpacked\SGR-Desktop.exe"
```

Se retornar `True`, o build foi bem-sucedido! ✅

O executável estará em:
```
D:\git\Desktop\SGR-Desktop\frontend\dist\win-unpacked\SGR-Desktop.exe
```

---

## Troubleshooting

### Erro: "A cadeia de caracteres não tem o terminador"

**Causa:** Problema de encoding no script PowerShell.

**Solução:** Use o script alternativo `build_sem_code_signing_v2.ps1` que não tem emojis.

### Erro: "Não foi possível remover cache"

**Causa:** Falta de permissões administrativas.

**Solução:** Execute o PowerShell como Administrador.

### Erro: "Executável não foi gerado"

**Causa:** Build falhou antes de gerar o executável.

**Solução:**
1. Verifique se o Flask foi gerado: `Test-Path "..\backend\dist\flask_server.exe"`
2. Verifique se o Flask foi copiado: `Test-Path "resources\flask_server.exe"`
3. Verifique os logs do build para mais detalhes

---

## Dicas Importantes

1. **Sempre execute como Administrador** quando for limpar o cache
2. **Limpe o cache antes de cada build** se o problema persistir
3. **Use o script alternativo** se o original não funcionar
4. **Verifique se o executável foi gerado** mesmo se houver avisos

---

## Próximos Passos

1. Limpe o cache do winCodeSign (como Administrador)
2. Execute o build
3. Verifique se o executável foi gerado
4. Teste o executável gerado

---

**Última atualização:** Dezembro 2024

