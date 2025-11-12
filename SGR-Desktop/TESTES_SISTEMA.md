# 🧪 Testes de Sistema - SGR Desktop

## 📋 Visão Geral

Este documento descreve os **testes de sistema** (System Tests) para o SGR Desktop. Estes testes verificam o sistema integrado como um todo, simulando o uso real pelos usuários finais.

---

## 🎯 Objetivo dos Testes de Sistema

**Verificação:** "Estamos construindo o produto corretamente?"

Os testes de sistema usam abordagem **Caixa-Preta** - testam o comportamento externo do sistema sem conhecer detalhes de implementação interna.

---

## 🔄 Fluxos de Teste Funcionais

### 1. Fluxo de Autenticação

**Objetivo:** Verificar processo completo de login e autenticação

**Passos:**
1. Abrir o SGR Desktop
2. Verificar se a tela de login é exibida
3. Tentar login com senha errada
   - **Esperado:** Mensagem de erro amigável
   - **Esperado:** Usuário permanece na tela de login
4. Fazer login com credenciais válidas
   - **Esperado:** Redirecionamento para dashboard
   - **Esperado:** Sidebar de navegação visível
5. Verificar se dados do restaurante são carregados
   - **Esperado:** Nome do restaurante exibido
   - **Esperado:** Dashboard com KPIs carregados

**Critérios de Sucesso:**
- ✅ Login bem-sucedido redireciona corretamente
- ✅ Erro de login exibe mensagem clara
- ✅ Sessão é mantida após login
- ✅ Logout limpa sessão e redireciona para login

---

### 2. Fluxo de Venda (PDV)

**Objetivo:** Verificar processo completo de registro de venda

**Passos:**
1. Logar como "Operador"
2. Navegar para "Gestão de Vendas" ou "PDV"
3. Iniciar um novo pedido
4. Adicionar 3 itens do cardápio:
   - Item 1: Hambúrguer (R$ 25,50)
   - Item 2: Refrigerante (R$ 5,00)
   - Item 3: Batata Frita (R$ 12,00)
5. Verificar cálculo do total:
   - **Esperado:** Total = R$ 42,50
6. Fechar o pedido e registrar pagamento
7. Verificar se o pedido aparece na "Fila de Pedidos"
   - **Esperado:** Pedido listado com status "PENDENTE"
   - **Esperado:** Valor total correto
   - **Esperado:** Itens corretos

**Critérios de Sucesso:**
- ✅ Cálculo de total está correto
- ✅ Pedido é criado na API
- ✅ Pedido aparece na fila imediatamente
- ✅ Status inicial é "PENDENTE"

---

### 3. Fluxo de Gestão (CRUD de Cardápio)

**Objetivo:** Verificar operações CRUD completas no cardápio

#### 3.1. Create (Criar)

**Passos:**
1. Logar como "Gestor"
2. Navegar para "Cardápio Dinâmico"
3. Clicar em "Adicionar Prato"
4. Preencher formulário:
   - Nome: "Pizza Margherita"
   - Descrição: "Pizza tradicional italiana"
   - Preço: R$ 35,00
   - Categoria: "PRATO_PRINCIPAL"
   - Imagem: (opcional)
5. Salvar
6. Verificar se o prato aparece na lista
   - **Esperado:** Prato listado com dados corretos
   - **Esperado:** Categoria formatada ("Prato Principal")

**Critérios de Sucesso:**
- ✅ Validação de campos obrigatórios funciona
- ✅ Prato é criado na API
- ✅ Prato aparece na lista imediatamente
- ✅ Dados exibidos estão corretos

#### 3.2. Read (Ler)

**Passos:**
1. Verificar se lista de pratos é carregada
2. Verificar se dados são exibidos corretamente:
   - Nome
   - Preço formatado (R$ X,XX)
   - Categoria formatada
   - Imagem (se disponível)

**Critérios de Sucesso:**
- ✅ Lista carrega todos os itens
- ✅ Dados são formatados corretamente
- ✅ Busca/filtro funciona

#### 3.3. Update (Atualizar)

**Passos:**
1. Clicar em "Editar" em um prato existente
2. Modal deve abrir com dados preenchidos
3. Alterar preço de R$ 35,00 para R$ 38,00
4. Salvar
5. Verificar se alteração aparece na lista
   - **Esperado:** Preço atualizado na lista
   - **Esperado:** Outros dados inalterados

**Critérios de Sucesso:**
- ✅ Modal abre com dados corretos
- ✅ Alteração é salva na API
- ✅ Lista é atualizada imediatamente

#### 3.4. Delete (Deletar)

**Passos:**
1. Clicar em "Excluir" em um prato
2. Confirmar exclusão
3. Verificar se prato desaparece da lista
   - **Esperado:** Prato removido da lista
   - **Esperado:** Prato deletado na API

**Critérios de Sucesso:**
- ✅ Confirmação de exclusão funciona
- ✅ Prato é removido da API
- ✅ Lista é atualizada imediatamente

---

### 4. Fluxo de Análise (Dashboard)

**Objetivo:** Verificar carregamento e exibição de dados analíticos

**Passos:**
1. Logar como "Gestor"
2. Navegar para "Dashboard"
3. Verificar se KPIs são carregados:
   - Total de Vendas
   - Quantidade de Produtos
   - Ticket Médio Diário
   - Evolução Percentual
4. Verificar se gráficos são renderizados:
   - Gráfico de Vendas Diárias (últimos 7 dias)
   - Gráfico de Produtos Vendidos (últimos 7 dias)
5. Verificar se dados são atualizados ao recarregar

**Critérios de Sucesso:**
- ✅ Todos os KPIs são exibidos
- ✅ Gráficos são renderizados (Chart.js)
- ✅ Dados são calculados corretamente
- ✅ Interface é responsiva

---

### 5. Fluxo de Gestão de Pedidos

**Objetivo:** Verificar atualização de status de pedidos

**Passos:**
1. Logar como "Gestor"
2. Navegar para "Gestão de Pedidos"
3. Verificar se lista de pedidos é carregada
4. Selecionar um pedido com status "PENDENTE"
5. Atualizar status para "EM_PREPARO"
6. Verificar se status é atualizado na lista
7. Atualizar status para "PRONTO"
8. Atualizar status para "ENTREGUE"
9. Verificar se pedido desaparece da lista de pendentes

**Critérios de Sucesso:**
- ✅ Lista de pedidos carrega corretamente
- ✅ Status é atualizado na API
- ✅ Interface reflete mudança imediatamente
- ✅ Filtros por status funcionam

---

## 🚀 Testes Não Funcionais

### 1. Desempenho (Performance)

**Teste:** Tempo de carregamento do Dashboard

**Método:**
1. Abrir DevTools (F12) → Network tab
2. Navegar para Dashboard
3. Medir tempo de carregamento:
   - **Meta:** < 2 segundos para carregar KPIs
   - **Meta:** < 3 segundos para renderizar gráficos

**Teste:** Performance com muitos dados

**Cenário:** Fila de Pedidos com 1000 pedidos

**Método:**
1. Simular 1000 pedidos na API
2. Navegar para "Gestão de Pedidos"
3. Verificar:
   - **Esperado:** Lista carrega em < 5 segundos
   - **Esperado:** Interface permanece responsiva
   - **Esperado:** Scroll funciona suavemente

---

### 2. Segurança

**Teste:** Controle de Acesso

**Cenário:** Usuário "Operador" tentando acessar rotas de "Administrador"

**Método:**
1. Logar como "Operador"
2. Tentar acessar funcionalidades administrativas
3. Verificar:
   - **Esperado:** Acesso negado ou funcionalidade oculta
   - **Esperado:** Mensagem de erro apropriada (se aplicável)

**Teste:** Validação de Sessão

**Método:**
1. Fazer login
2. Aguardar 30 minutos (simular sessão expirada)
3. Tentar fazer requisição
4. Verificar:
   - **Esperado:** Redirecionamento para login
   - **Esperado:** Mensagem de sessão expirada

---

### 3. Compatibilidade (Windows)

**Teste:** Instalação no Windows

**Método:**
1. Executar instalador `.exe`
2. Seguir assistente de instalação
3. Verificar:
   - **Esperado:** Instalação completa sem erros
   - **Esperado:** Atalho criado no Menu Iniciar
   - **Esperado:** Aplicativo abre corretamente

**Teste:** Execução no Windows

**Método:**
1. Abrir aplicativo instalado
2. Verificar:
   - **Esperado:** Janela abre com tamanho correto (1400x900)
   - **Esperado:** Interface renderiza corretamente
   - **Esperado:** Navegação funciona
   - **Esperado:** Gráficos são exibidos

---

### 4. Usabilidade

**Teste:** Interface Responsiva

**Método:**
1. Redimensionar janela do aplicativo
2. Verificar:
   - **Esperado:** Layout se adapta ao tamanho
   - **Esperado:** Elementos não ficam sobrepostos
   - **Esperado:** Scroll funciona quando necessário

**Teste:** Intuitividade para Operador

**Método:**
1. Pedir a um operador de caixa (usuário real) para:
   - Fazer login
   - Registrar um pedido
   - Atualizar status de um pedido
2. Observar:
   - **Esperado:** Operador consegue realizar tarefas sem treinamento extensivo
   - **Esperado:** Botões são claros e intuitivos
   - **Esperado:** Mensagens de erro são compreensíveis

---

## 📝 Testes de Aceitação (UAT)

### Para Gestores

**Tarefa:** "Feche o caixa do dia e veja o relatório de quais pratos mais venderam."

**Passos esperados do usuário:**
1. Fazer login como gestor
2. Navegar para Dashboard
3. Verificar KPIs do dia
4. Navegar para "Gestão de Vendas"
5. Filtrar por período (hoje)
6. Verificar top produtos

**Critérios de Aceitação:**
- ✅ Usuário consegue completar tarefa em < 5 minutos
- ✅ Dados exibidos são precisos
- ✅ Interface é clara e fácil de usar

---

### Para Operadores

**Tarefa:** "Um cliente ligou, registre o pedido dele para entrega."

**Passos esperados do usuário:**
1. Fazer login como operador
2. Navegar para área de pedidos/PDV
3. Criar novo pedido
4. Adicionar itens do cardápio
5. Registrar dados do cliente (nome, telefone, endereço)
6. Finalizar pedido

**Critérios de Aceitação:**
- ✅ Usuário consegue completar tarefa em < 3 minutos
- ✅ Processo é intuitivo
- ✅ Dados são salvos corretamente

---

## 📊 Checklist de Testes de Sistema

### Funcionalidades Principais

- [ ] Login e autenticação
- [ ] Dashboard com KPIs e gráficos
- [ ] CRUD completo de cardápio
- [ ] Gestão de pedidos (criar, atualizar status)
- [ ] Gestão de vendas (relatórios, top produtos)
- [ ] Avaliações (visualizar, filtrar)

### Integrações

- [ ] Frontend ↔️ Backend (Flask)
- [ ] Backend ↔️ API Externa (Java)
- [ ] Persistência de sessão (cookies)
- [ ] Tratamento de erros de rede

### Não Funcionais

- [ ] Performance (tempo de carregamento)
- [ ] Segurança (controle de acesso)
- [ ] Compatibilidade Windows
- [ ] Usabilidade (interface intuitiva)

---

## 🎯 Critérios de Sucesso Geral

O sistema está pronto para produção quando:

1. ✅ Todos os fluxos funcionais passam
2. ✅ Performance atende aos requisitos (< 3s para carregar)
3. ✅ Segurança está implementada
4. ✅ Testes de aceitação com usuários reais são aprovados
5. ✅ Não há bugs críticos ou bloqueadores

---

## 📚 Documentação Relacionada

- **Testes Unitários:** `backend/tests/README_TESTES.md`
- **Testes de Integração:** `backend/tests/test_integration_*.py`
- **Instruções de Desenvolvimento:** `INSTRUCOES_DESENVOLVIMENTO.md`

---

**Última atualização:** Dezembro 2024

