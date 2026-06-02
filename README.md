# jira-dev

Skill do Claude Code para desenvolvedores: pesquisa de contexto no Jira, criação e documentação de tickets (histórias, bugs, tarefas, subtarefas).

---

## O que essa skill faz

- **Pesquisa** regras de negócio, critérios de aceite, cenários de teste e comentários em linguagem natural
- **Cria** histórias, bugs, tarefas e subtarefas com descrição estruturada
- **Documenta** tickets existentes adicionando seções que ainda não foram preenchidas (nunca apaga conteúdo)
- **Comenta** em tickets para registrar decisões e alinhamentos
- **Lê** o campo GMUD (link da PR) de épicos

---

## Permissões

| Operação | Permitido |
|---|---|
| Pesquisar qualquer issue | Sim |
| Criar histórias, bugs, tarefas, subtarefas | Sim |
| Documentar descrição, critérios de aceite, cenários de teste | Sim |
| Adicionar comentários | Sim |
| Ler GMUD (link da PR) de épicos | Sim |
| **Criar épicos** | **Não** |
| **Ler campos de ciclo de vida de épicos** | **Não** |
| **Sobrescrever campos já preenchidos** | **Não** |

---

## Pré-requisitos

- [Claude Code](https://claude.ai/code) instalado
- Python 3.8 ou superior
- Biblioteca `requests`: `pip install requests`
- Conta Atlassian com acesso de leitura e escrita ao Jira (`qx3prod.atlassian.net`)
- Token de API do Jira ([gerar aqui](https://id.atlassian.com/manage-profile/security/api-tokens))

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

### 2. Configure as variáveis de ambiente

Abra (ou crie) o arquivo `~/.claude/settings.json` e adicione:

```json
{
  "env": {
    "JIRA_EMAIL": "seu-email@empresa.com",
    "JIRA_API_TOKEN": "seu-token-de-api-aqui"
  }
}
```

> Como gerar o token Jira: https://id.atlassian.com/manage-profile/security/api-tokens

### 3. Instale as dependências Python

```bash
pip install requests
```

### 4. Reinicie o Claude Code

Feche e reabra o Claude Code para carregar a skill.

---

## Como usar

```
"Qual a regra de negócio do campo CCEE?"
"Cria uma história no TPROJ: Como usuário, quero ver minha fatura online"
"Adiciona critério de aceite no TPROJ-123"
"Documenta a história TPROJ-456 com esse contexto: ..."
"Qual o link da PR do épico TPROJ-100?"
"Quais histórias falam de reforma tributária?"
"Cria um bug no TLIGHTDIST: tela de fatura quebrando ao abrir PDF"
"Comenta no TPROJ-123: alinhado com o Sartor na reunião de hoje"
```

---

## Estrutura do projeto

```
jira-dev/
├── SKILL.md              # Definição da skill (lida pelo Claude)
├── scripts/
│   └── jira_dev.py       # Funções de API, pesquisa, criação e documentação
└── README.md
```

---

## Integração com outras skills

Esta skill é complementar às outras skills Jira:

| Skill | Para que serve |
|---|---|
| `jira-analytics` | Análise de sprints, métricas de time, saúde de épicos — somente leitura |
| `jira-epic-automator` | Ciclo de vida de épicos: Quarter, datas, garantia, status — escrita controlada |
| `jira-dev` | Criação e documentação de tickets do dia a dia do time de desenvolvimento |

---

## Segurança

- As credenciais ficam em `~/.claude/settings.json` — **nunca** as adicione ao repositório
- Campos já preenchidos nunca são sobrescritos
- Épicos não podem ser criados por esta skill
- Campos de ciclo de vida de épicos (Quarter, datas, garantia) não são acessíveis
