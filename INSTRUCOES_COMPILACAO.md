# 🚀 Instruções Rápidas de Compilação

## ⚡ Compilação Rápida (3 comandos)

```bash
# 1. Navegue até a pasta frontend
cd SGR-Desktop/frontend

# 2. Instale o electron-builder (apenas primeira vez)
npm install --save-dev electron-builder

# 3. Compile o aplicativo
npm run build
```

**Pronto!** O executável estará em: `frontend/dist/`

---

## 📦 O que será gerado?

Após executar `npm run build`, você terá:

```
SGR-Desktop/frontend/dist/
├── SGR-Desktop Setup 1.0.0.exe  ← Windows (instalador)
└── win-unpacked/                 ← Windows (pasta descompactada para testar)
```

---

## 🧪 Como testar

1. Execute o arquivo `.exe` gerado em `dist/`
2. O instalador será aberto
3. Instale o aplicativo
4. Abra o aplicativo instalado e teste

---

## ⚠️ Antes de Compilar

Certifique-se de que:

- ✅ **Node.js** está instalado (versão 16+)
- ✅ **Python** está instalado (para backend)
- ✅ **PostgreSQL** está rodando
- ✅ Você está na pasta `frontend`

---

## 🐛 Problemas Comuns

### Erro: "electron-builder not found"
```bash
npm install --save-dev electron-builder
```

### Executável muito grande?
Normal! Electron inclui o runtime completo (~80-150 MB).

### Quer gerar apenas para Windows?
```bash
npm run build --win
```

---

## 📚 Documentação Completa

Para mais detalhes, consulte: **`COMPILACAO_FINAL.md`**

---

**🎯 Objetivo:** Gerar um `.exe` que seus clientes possam instalar sem precisar de Python ou Node.js!

**✨ Produto Final:** Um aplicativo totalmente autônomo e profissional!
