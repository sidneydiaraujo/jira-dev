# jira-dev

Skill do Claude Code para desenvolvedores: pesquisa de contexto no Jira, criação e documentação de tickets (histórias, bugs, tarefas, subtarefas).

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
| Apagar campos que você preencheu | ✅ |
| Criar épicos | ❌ |
| Escrever em tickets de outros desenvolvedores | ❌ |
| Alterar Complexidade, campo IA ou campo Pai | ❌ |
| Acessar dados de ciclo de vida de épicos | ❌ |
| Deletar tickets | ❌ |

> A skill só permite escrever em tickets onde **você é o assignee**. Qualquer tentativa em ticket de outra pessoa é bloqueada automaticamente.

---

## Pré-requisitos

- [Claude Code](https://claude.ai/code) instalado (desktop, CLI ou extensão de IDE)
- Python 3.8 ou superior
- Biblioteca `requests` instalada
- Conta Atlassian com acesso ao Jira `qx3prod.atlassian.net`
- Token de API do Jira — [gerar aqui](https://id.atlassian.com/manage-profile/security/api-tokens)

---

## Instalação

### 1. Clone o repositório na pasta de skills do Claude

**macOS / Linux:**
```bash
mkdir -p ~/.claude/skills
cd ~/.claude/skills
git clone https://github.com/sidneydiaraujo/jira-dev
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills"
cd "$env:USERPROFILE\.claude\skills"
git clone https://github.com/sidneydiaraujo/jira-dev
```

### 2. Instale as dependências Python

```bash
pip install requests
```

### 3. Configure as credenciais do Jira

Você precisa adicionar suas credenciais ao arquivo de configuração do Claude Code.

**Localize o arquivo `settings.json`:**

| Sistema | Caminho |
|---|---|
| Windows | `C:\Users\<seu-usuario>\.claude\settings.json` |
| macOS / Linux | `~/.claude/settings.json` |

**Se o arquivo não existir**, crie-o com este conteúdo:

```json
{
  "env": {
    "JIRA_EMAIL": "seu-email@thunders.com.br",
    "JIRA_API_TOKEN": "seu-token-de-api-aqui"
  }
}
```

**Se o arquivo já existir** (você já tem outras skills ou configurações), **adicione apenas o bloco `env`** sem apagar o restante. Exemplo de merge correto:

```json
{
  "model": "sonnet",
  "env": {
    "JIRA_EMAIL": "seu-email@thunders.com.br",
    "JIRA_API_TOKEN": "seu-token-de-api-aqui"
  }
}
```

> ⚠️ Nunca substitua o arquivo inteiro — isso apaga configurações existentes de outras skills.

### 4. Reinicie o Claude Code

Feche e reabra o Claude Code para carregar a skill. Na lista de skills disponíveis, `jira-dev` deve aparecer.

---

## Como usar

A skill entende linguagem natural. Não é necessário saber a sintaxe exata.

### Pesquisa

```
"Qual a regra de negócio do campo CCEE?"
"O que foi combinado sobre a integração com SAP?"
"Quais histórias falam de reforma tributária?"
"Tem critério de aceite para fatura de venda?"
"O que foi decidido sobre garantia nos comentários?"
```

### Listar suas estórias

```
"Procure estórias com a minha responsabilidade"
"Quais são minhas histórias em andamento?"
"Lista meus bugs abertos"
```

### Criar tickets

```
"Cria uma história no TPROJ: Como usuário, quero ver minha fatura online"
"Cria um bug no TLIGHTDIST: tela de fatura quebrando ao abrir PDF"
"Adiciona uma subtarefa no TPROJ-123: Criar endpoint"
```

### Documentar tickets

Se você não informar a chave do ticket, a skill lista suas estórias Em Andamento para você escolher:

```
"Adiciona critério de aceite na minha estória"
"Documenta a TPROJ-123 com esse contexto: ..."
"Adiciona cenários de teste no TPROJ-456"
```

### Editar campos

```
"Muda a prioridade da TPROJ-123 para Alta"
"Altera o resumo da TPROJ-123 para: novo título"
"Apaga a descrição da TPROJ-123"
```

### Apontar horas

```
"Finalizei o Criar domínio, dê baixa nas horas e conclua a subtarefa"
"Aponta 3h de hoje no TPROJ-11157"
"Registra 1h 30m no TPROJ-456 com observação: revisão de código"
```

### Transição de status

```
"Move a TPROJ-123 para Em Andamento"
"Conclui a TPROJ-456"
"Coloca a TPROJ-789 em Backlog"
```

---

## Estrutura do projeto

```
jira-dev/
├── SKILL.md              # Definição da skill (lida pelo Claude)
├── scripts/
│   └── jira_dev.py       # Funções de API, pesquisa, criação e documentação
├── .gitignore
└── README.md
```

---

## Integração com outras skills Jira

| Skill | Para que serve |
|---|---|
| [`jira-analytics`](https://github.com/sidneydiaraujo/jira-analytics) | Análise de sprints, métricas de time, saúde de épicos — somente leitura |
| [`jira-epic-automator`](https://github.com/sidneydiaraujo/jira-epic-automator) | Ciclo de vida de épicos: Quarter, datas, garantia, status |
| `jira-dev` | Criação e documentação de tickets do dia a dia do time |

---

## Segurança

- As credenciais ficam **apenas** em `settings.json` local — nunca no repositório
- A skill só escreve em tickets onde você é o `assignee`
- Campos bloqueados por política (Complexidade, IA, Pai) nunca são alterados
- Campos já preenchidos não são sobrescritos sem solicitação explícita
- Nenhuma operação de deleção está disponível na skill
