---
name: jira-dev
description: "Skill para desenvolvedores: pesquisa de contexto no Jira, criacao e documentacao de tickets. Use esta skill quando o usuario quiser criar historias, bugs, tarefas ou subtarefas no Jira, documentar criterios de aceite, cenarios de teste ou descricao de um ticket, pesquisar regras de negocio ou combinados em issues existentes, adicionar comentarios, ou consultar o link da PR (GMUD) de um epico. Acione para frases como: 'cria uma historia no TPROJ', 'documenta esse ticket', 'adiciona criterio de aceite no TPROJ-123', 'qual a regra de negocio de X?', 'cria um bug para o epico TPROJ-100', 'adiciona cenario de teste no ticket', 'comenta no TPROJ-456', 'qual o link da PR do epico?', 'pesquisa sobre reforma tributaria no jira', 'o que esta escrito sobre garantia nos tickets'. Esta skill NAO lida com epicos nem com dados analiticos de sprint — para isso use jira-epic-automator ou jira-analytics."
---

# Jira Dev

Skill para desenvolvedores: pesquisa de contexto no Jira, criacao e documentacao de tickets (historias, bugs, tarefas, subtarefas).

**Projetos monitorados:** TPROJ, TNP, TLIGHTDIST, TLIGHTCOM, THP, TTRD, TSRV, PROJTHUN, SUP, TVAR

**Script principal:** `scripts/jira_dev.py`

---

## Permissoes

| Operacao | Permitido |
|---|---|
| Pesquisar qualquer issue (historia, bug, tarefa) | Sim |
| Ler descricao, criterios de aceite, comentarios | Sim |
| Criar historias, bugs, tarefas, subtarefas | Sim |
| Documentar descricao, criterios de aceite, cenarios de teste | Sim |
| Adicionar comentarios | Sim |
| Ler campo GMUD (link da PR) de epicos | Sim |
| **Criar epicos** | **Nao** |
| **Ler campos de ciclo de vida de epicos** | **Nao** |
| **Editar qualquer campo de epico (exceto GMUD)** | **Nao** |
| **Sobrescrever campos ja preenchidos** | **Nao** |

### Campos de epico BLOQUEADOS (nunca ler, nunca escrever)

Quarter, Start Date, Data Limite, Data de Publicacao, Data de Garantia, Ciclos de Garantia, Responsavel Handover, Fix Versions, status do epico.

O UNICO campo de epico acessivel e o GMUD (link da PR).

---

## Regra Principal — Nunca Sobrescrever

Antes de qualquer escrita, a skill verifica o campo atual:
- **Campo vazio:** preenche normalmente.
- **Campo ja preenchido:** informa o valor existente e NAO altera nada.
- **Excecao:** comentarios sao sempre adicionados (nunca sobrescrevem).

---

## Pesquisa de Contexto

**Gatilhos:** "qual a regra de negocio de", "qual o criterio de aceite de", "o que foi combinado sobre", "tem cenario de teste para", "busca sobre", "o que esta escrito sobre", "pesquisa no jira", "quais historias falam de"

```python
from scripts.jira_dev import search_content
result = search_content(query, project_keys=None, days=None, max_results=20)
```

Pesquisa dentro de:
- **Descricoes** — regras de negocio, requisitos, detalhamento
- **Criterios de aceite** — blocos AC:, acceptance criteria
- **Cenarios de teste** — BDD/Gherkin, Dado que / Quando / Entao
- **Comentarios** — decisoes, combinados, alinhamentos

Formato de retorno: `key, resumo, tipo, status, responsavel, matches` com trecho contextualizado.

### Exemplos de pesquisa

```
"qual a regra de calculo do CCEE?"
"criterio de aceite para fatura de venda"
"o que foi combinado sobre integracao com SAP?"
"cenarios de teste de migracao de ativo"
"qual regra de negocio para garantia?"
```

---

## Leitura de Issues

**Gatilhos:** "mostra o ticket", "abre o TPROJ-XXX", "qual o status de", "leia o ticket"

```python
from scripts.jira_dev import get_issue
issue = get_issue("TPROJ-123")
```

Retorna: resumo, tipo, status, responsavel, descricao, criterios de aceite, comentarios, subtarefas.

Para epicos: mostra apenas GMUD. Campos de ciclo de vida sao omitidos automaticamente.

### Ler GMUD de um epico

```python
from scripts.jira_dev import get_epic_gmud
gmud = get_epic_gmud("TPROJ-100")
# retorna: {"key": "TPROJ-100", "resumo": "...", "gmud": "https://..."}
```

---

## Criacao de Tickets

**Gatilhos:** "cria uma historia", "cria um bug", "cria uma tarefa", "cria uma subtarefa", "crie o ticket", "adiciona uma historia no epico"

```python
from scripts.jira_dev import create_issue
result = create_issue(
    project_key="TPROJ",
    summary="Como usuario, quero...",
    issuetype="Historia",       # Historia | Bug | Tarefa | Subtarefa
    description="Contexto da funcionalidade...",
    acceptance_criteria="AC1: ...\nAC2: ...",
    test_scenarios="Dado que...\nQuando...\nEntao...",
    epic_link="TPROJ-100",      # opcional
    parent_key=None,            # para subtarefas
    assignee_account_id=None,   # opcional
    labels=None,                # opcional
    priority=None               # opcional: Alta | Media | Baixa
)
```

### Tipos de issue validos

| Nome | Quando usar |
|---|---|
| Historia | Funcionalidade do usuario (user story) |
| Bug | Defeito ou comportamento incorreto |
| Tarefa | Trabalho tecnico sem valor direto ao usuario |
| Subtarefa | Divisao de uma historia ou tarefa em partes menores |

**Nunca crie epicos** — use a skill `jira-epic-automator` para gestao de epicos.

### Como perguntar o contexto antes de criar

Antes de criar um ticket, pergunte ao usuario:
1. Qual projeto? (se nao informado, perguntar)
2. Qual tipo? (Historia, Bug, Tarefa, Subtarefa)
3. Qual o titulo/resumo?
4. Este ticket pertence a algum epico ou historia pai?
5. Ha descricao, criterios de aceite ou cenarios de teste para incluir?

---

## Documentacao de Tickets Existentes

**Gatilhos:** "documenta o ticket", "adiciona criterio de aceite no", "escreve a descricao do", "adiciona cenario de teste no", "preenche os campos do", "documenta a historia"

```python
from scripts.jira_dev import update_description
result = update_description(
    issue_key="TPROJ-123",
    description="Contexto...",            # opcional — so preenche se vazio
    acceptance_criteria="AC1: ...",       # opcional — so preenche se secao nao existe
    test_scenarios="Dado que..."          # opcional — so preenche se secao nao existe
)
```

A funcao detecta automaticamente quais secoes ja existem na descricao e apenas adiciona as que estiverem faltando. **Nunca apaga conteudo existente.**

---

## Comentarios

**Gatilhos:** "adiciona um comentario no", "comenta no ticket", "registra no ticket", "anota no ticket"

```python
from scripts.jira_dev import add_comment
result = add_comment("TPROJ-123", "Texto do comentario aqui.")
```

Comentarios sao sempre adicionados — nunca sobrescrevem comentarios existentes.

---

## Busca de Usuarios

```python
from scripts.jira_dev import find_user
users = find_user("Anderson")
# retorna: [{"accountId": "...", "nome": "Anderson ...", "email": "..."}]
```

Use quando o usuario informar o nome de quem deve ser atribuido ao ticket.

---

## Como Esta Skill Responde

- **Pesquisa:** tabela com key, resumo, tipo, status, responsavel + trechos encontrados
- **Leitura:** resumo formatado do ticket com todos os campos visiveis
- **Criacao:** confirmacao com key gerada e link direto para o ticket
- **Documentacao:** confirmar quais secoes foram adicionadas e quais ja existiam
- **Erro de campo bloqueado:** explicar que o campo pertence ao ciclo de vida do epico e sugerir usar a jira-epic-automator

---

## Exemplos de Uso

| O usuario diz | Acao |
|---|---|
| "qual a regra de negocio do campo CCEE?" | `search_content("regra negocio campo CCEE")` |
| "quais historias falam de reforma tributaria?" | `search_content("reforma tributaria")` |
| "abre o TPROJ-123" | `get_issue("TPROJ-123")` |
| "qual o link da PR do epico TPROJ-100?" | `get_epic_gmud("TPROJ-100")` |
| "cria uma historia no TPROJ para o epico TPROJ-100" | perguntar resumo + contexto → `create_issue(...)` |
| "cria um bug no TLIGHTDIST: tela de fatura quebrando" | `create_issue("TLIGHTDIST", "Tela de fatura quebrando", "Bug", ...)` |
| "adiciona criterio de aceite no TPROJ-123" | `update_description("TPROJ-123", acceptance_criteria="...")` |
| "documenta a historia TPROJ-456 com esse contexto: ..." | `update_description("TPROJ-456", description="...", ...)` |
| "comenta no TPROJ-123: alinhado com o time" | `add_comment("TPROJ-123", "alinhado com o time")` |
| "qual o tipo de issue disponivel no TPROJ?" | `get_issue_types("TPROJ")` |

---

## Tratamento de Erros

- **Campo ja preenchido:** informa o valor atual, nao altera nada
- **Tentativa de criar epico:** bloqueia e orienta a usar jira-epic-automator
- **Tentativa de ler campo bloqueado de epico:** informa que o campo e de ciclo de vida e nao esta disponivel
- **Issue nao encontrado:** pedir confirmacao da chave com o usuario
- **Usuario nao encontrado:** pedir nome completo ou email
- **401/403:** verificar JIRA_EMAIL e JIRA_API_TOKEN no settings.json
