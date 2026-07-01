# jira-dev

Skill do Claude Code para desenvolvedores: pesquisa de contexto no Jira, criação e documentação de tickets (histórias, bugs, tarefas, subtarefas).

> **Sem configuração de token.** Esta skill usa o conector Atlassian nativo do Claude. Cada desenvolvedor autentica com a própria conta — basta habilitar o plugin uma vez.

---

## O que essa skill faz

| Capacidade | Exemplos |
|---|---|
| **Pesquisa** | Regras de negócio, critérios de aceite, cenários de teste, comentários |
| **Leitura** | Abre qualquer ticket com todos os campos visíveis |
| **Criação** | Histórias, bugs, tarefas e subtarefas com descrição estruturada |
| **Documentação** | Preenche descrição, critérios de aceite e cenários de teste nos campos corretos |
| **Edição** | Altera qualquer campo permitido (prioridade, resumo, sprint, labels…) |
| **Apontamento de horas** | Registra worklog com data e tempo no controle de horas |
| **Transição de status** | Move tickets entre status por nome |
| **Seletor de estória** | Lista suas estórias Em Andamento para escolher sem precisar lembrar a chave |
| **GMUD** | Lê o campo GMUD (link da PR) de épicos |

---

## Permissões

| Operação | Permitido |
|---|---|
| Pesquisar e ler qualquer issue | ✅ |
| Criar histórias, bugs, tarefas, subtarefas | ✅ |
| Editar e documentar tickets **onde você é o responsável** | ✅ |
| Apontar horas em tickets seus | ✅ |
| Criar épicos | ❌ |
| Escrever em tickets de outros desenvolvedores | ❌ |
| Alterar Complexidade, campo IA ou campo Pai | ❌ |
| Acessar dados de ciclo de vida de épicos | ❌ |
| Deletar tickets | ❌ |

> A skill só permite escrever em tickets onde **você é o assignee**. Qualquer tentativa em ticket de outra pessoa é bloqueada automaticamente.

---

## Instalação

### Pré-requisitos

- [Claude Code](https://claude.ai/code) instalado (desktop, CLI ou extensão de IDE)
- Conta Atlassian com acesso ao Jira `qx3prod.atlassian.net`

Não é necessário Python, pip ou token de API.

---

### Passo 1 — Instale o Claude Code

Se ainda não tiver o Claude Code instalado:

**Windows:**
```powershell
winget install Anthropic.ClaudeCode
```

**macOS:**
```bash
brew install claude-code
```

Ou baixe o instalador em [claude.ai/code](https://claude.ai/code).

---

### Passo 2 — Habilite o plugin Atlassian no Claude

O plugin Atlassian permite que o Claude acesse o Jira com a sua conta.

1. Abra o Claude Code
2. Digite `/plugins` no chat **ou** acesse **Settings → Plugins**
3. Localize **Atlassian Rovo** na lista
4. Clique em **Habilitar** / **Enable**
5. Uma janela de login Atlassian vai abrir — entre com sua conta corporativa (`@thunders.com.br`)
6. Autorize o acesso ao Jira quando solicitado

> Se o plugin não aparecer na lista, confirme com o administrador do Claude Code da organização se o Atlassian Rovo está liberado no plano.

---

### Passo 3 — Copie a skill para a pasta do Claude

**Windows (PowerShell):**
```powershell
# Cria a pasta de skills se não existir
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills"

# Clona a skill
cd "$env:USERPROFILE\.claude\skills"
git clone https://github.com/sidneydiaraujo/jira-dev
```

**macOS / Linux:**
```bash
mkdir -p ~/.claude/skills
cd ~/.claude/skills
git clone https://github.com/sidneydiaraujo/jira-dev
```

> Sem Git? Baixe o ZIP pelo GitHub (`Code → Download ZIP`), extraia e mova a pasta `jira-dev` para `~/.claude/skills/`.

---

### Passo 4 — Reinicie o Claude Code

Feche e reabra o Claude Code. A skill `jira-dev` vai aparecer na lista de skills disponíveis.

Para confirmar, digite no chat:
```
/jira-dev quais são minhas estórias em andamento?
```

Se o Claude listar seus tickets, a instalação está completa.

---

### Solução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| Skill não aparece na lista | Pasta não está em `~/.claude/skills/jira-dev/` | Verifique o caminho e reinicie |
| "Plugin Atlassian não encontrado" | Plugin não habilitado | Siga o Passo 2 novamente |
| "Não autorizado" ao acessar tickets | Conta logada não tem acesso ao projeto | Confirme com o admin do Jira |
| "Conector indisponível" | Sessão expirada | Faça logout e login novamente no plugin Atlassian |

---

## Como usar

A skill entende linguagem natural — não é necessário saber a sintaxe exata.

### Pesquisar contexto

```
"Qual a regra de negócio do campo CCEE?"
"O que foi combinado sobre a integração com SAP?"
"Quais histórias falam de reforma tributária?"
"Tem critério de aceite para fatura de venda?"
```

### Listar suas estórias

```
"Quais são minhas histórias em andamento?"
"Lista meus bugs abertos"
"Mostra todas as minhas tarefas"
```

### Criar tickets

```
"Cria uma história no TPROJ: Como usuário, quero ver minha fatura online"
"Cria um bug no TLIGHTDIST: tela de fatura quebrando ao abrir PDF"
"Adiciona uma subtarefa no TPROJ-123: Criar endpoint de consulta"
```

### Documentar tickets

Se você não informar a chave do ticket, a skill lista suas estórias Em Andamento para escolher:

```
"Adiciona critério de aceite na minha estória"
"Documenta a TPROJ-123 com esse contexto: ..."
"Adiciona cenários de teste no TPROJ-456"
```

### Editar campos

```
"Muda a prioridade da TPROJ-123 para Alta"
"Altera o resumo da TPROJ-123 para: novo título"
"Troca o responsável da TPROJ-456 para Anderson"
```

### Apontar horas

```
"Aponta 3h de hoje no TPROJ-11157"
"Registra 1h 30m no TPROJ-456 com observação: revisão de código"
"Lança 2h no TPROJ-789"
```

### Transição de status

```
"Move a TPROJ-123 para Em Andamento"
"Conclui a TPROJ-456"
"Coloca a TPROJ-789 em Em Testes"
```

---

## Estrutura do projeto

```
jira-dev/
├── SKILL.md        ← instruções da skill (lidas pelo Claude)
├── README.md       ← este arquivo
└── .gitignore
```

> Não há scripts Python nesta versão. Toda comunicação com o Jira é feita pelo conector Atlassian do Claude.

---

## Integração com outras skills Jira

| Skill | Para que serve |
|---|---|
| [`jira-analytics`](https://github.com/sidneydiaraujo/jira-analytics) | Análise de sprints, métricas de time, horas apontadas — somente leitura |
| [`jira-epic-automator`](https://github.com/sidneydiaraujo/jira-epic-automator) | Ciclo de vida de épicos: Quarter, datas, garantia, status |
| `jira-dev` | Criação e documentação de tickets do dia a dia do time |

---

## Segurança

- Nenhuma credencial é armazenada localmente — a autenticação é feita pelo plugin Atlassian do Claude
- A skill só escreve em tickets onde você é o `assignee`
- Campos bloqueados por política (Complexidade, IA, Pai, campos de épico) nunca são alterados
- Campos já preenchidos não são sobrescritos sem solicitação explícita
- Nenhuma operação de deleção está disponível
