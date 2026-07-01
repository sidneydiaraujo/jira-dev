---
name: jira-dev
description: "Skill para desenvolvedores: pesquisa de contexto no Jira, criacao e documentacao de tickets (historias, bugs, tarefas, subtarefas). Usa o conector Atlassian do Claude — sem configuracao de token necessaria. Cada usuario autentica com a propria conta Atlassian. Acione para: 'cria uma historia no TPROJ', 'documenta meu ticket', 'adiciona criterio de aceite no TPROJ-123', 'qual a regra de negocio do campo CCEE?', 'abre o TPROJ-123', 'comenta no ticket', 'aponta 3h no TPROJ-456', 'muda status para Em Testes', 'quais minhas estorias em andamento?'. Esta skill NAO lida com epicos nem dados de sprint — use jira-epic-automator ou jira-analytics para isso."
---

# Jira Dev

Skill para desenvolvedores: pesquisa de contexto, leitura e documentacao de tickets no Jira.

**Projetos monitorados:** TPROJ, TNP, TLIGHTDIST, TLIGHTCOM, THP, TTRD, TSRV, PROJTHUN, SUP, TVAR

**Autenticacao:** usa o conector Atlassian nativo do Claude (`mcp__claude_ai_Atlassian_Rovo__*`). Cada usuario autentica com a propria conta Jira — sem API token, sem configuracao adicional.

---

## Ferramentas disponíveis (conector Atlassian)

| Acao | Ferramenta MCP |
|---|---|
| Ler issue | `getJiraIssue(issueIdOrKey)` |
| Buscar por JQL | `searchJiraIssuesUsingJql(jql, fields, maxResults)` |
| Criar issue | `createJiraIssue(...)` |
| Editar campos | `editJiraIssue(issueIdOrKey, ...)` |
| Comentar | `addCommentToJiraIssue(issueIdOrKey, comment)` |
| Apontar horas | `addWorklogToJiraIssue(issueIdOrKey, timeSpent, ...)` |
| Transicionar status | `getTransitionsForJiraIssue` + `transitionJiraIssue` |
| Buscar usuario | `lookupJiraAccountId(query)` |
| Usuario atual | `atlassianUserInfo` |
| Tipos de issue | `getJiraProjectIssueTypesMetadata(projectKey)` |

---

## Permissoes

| Operacao | Permitido |
|---|---|
| Pesquisar qualquer issue | Sim |
| Ler descricao, criterios de aceite, comentarios | Sim |
| Criar historias, bugs, tarefas, subtarefas | Sim |
| Documentar descricao, criterios de aceite, cenarios de teste | Sim |
| Adicionar comentarios e worklogs | Sim |
| Ler campo GMUD (link da PR) de epicos | Sim |
| **Criar epicos** | **Nao** |
| **Editar epicos** | **Nao** |
| **Sobrescrever campos ja preenchidos sem confirmacao** | **Nao** |

---

## Regras de Seguranca

### 1. Verificacao de propriedade (obrigatoria antes de qualquer escrita)

Antes de QUALQUER escrita (editar campo, apontar horas, transicionar status):

1. Chamar `atlassianUserInfo` para obter o usuario atual
2. Chamar `getJiraIssue` para verificar o assignee do issue
3. Bloquear se:
   - Issue for um **Epico** → "Esta skill nao escreve em epicos."
   - Assignee for **diferente** do usuario atual → "Voce nao e o responsavel por [KEY]. Responsavel atual: [NOME]."
   - Issue **sem responsavel** → "Este issue nao tem responsavel. Atribua-se primeiro no Jira."

### 2. Campos bloqueados — nunca ler nem escrever

**Campos de ciclo de vida de epicos (nunca tocar):**

| Campo | ID |
|---|---|
| Quarter | customfield_11450 |
| Start Date | customfield_11201 |
| Data Limite | duedate |
| Data de Publicacao | customfield_11336 |
| Data de Garantia | customfield_12132 |
| Ciclos de Garantia | customfield_12131 |
| Responsavel Handover | customfield_12167 |
| Fix Versions | fixVersions |

**Campos bloqueados em qualquer issue:**

| Campo | Motivo |
|---|---|
| parent | Estrutura do backlog — impacta todo o epico |
| customfield_12368 | Complexidade — definido em refinamento |
| customfield_12436 | Campo de politica IA — bloqueado |
| issuetype | Alteracao estrutural que corrompe o workflow |
| fixVersions | Gerenciado exclusivamente pelo jira-epic-automator |

### 3. Nunca sobrescrever

Antes de editar qualquer campo:
- Leia o valor atual com `getJiraIssue`
- Se ja estiver preenchido: informe o valor existente e **nao altere nada**
- Excecao: comentarios e worklogs sao sempre adicionados (nunca sobrescrevem)

---

## IDs de Campos Customizados Importantes

| Nome amigavel | ID do campo |
|---|---|
| Criterios de Aceitacao | customfield_11208 |
| Cenarios de Testes | customfield_11537 |
| GMUD (link PR) | customfield_10902 |
| Epic Link | customfield_10014 |
| Sprint | customfield_10016 |
| Time | customfield_10600 |
| Tipo de Erro | customfield_11429 |
| DoD | customfield_11209 |
| DoR | customfield_12266 |
| Criterios Tecnicos | customfield_11568 |
| Evidencias de Testes | customfield_12200 |
| Evidencias Tecnicas | customfield_12233 |

---

## Seletor de Estoria

**Quando usar:** usuario quer documentar, editar ou apontar horas mas NAO informou a chave do ticket.

1. Executar:
```
searchJiraIssuesUsingJql(
  "assignee = currentUser() AND issuetype in (Historia, Story) AND status = 'Em Andamento' ORDER BY updated DESC",
  maxResults=20
)
```
2. Exibir lista numerada:
```
Suas estórias Em Andamento:

  1. TPROJ-11150 — titulo da historia     [Alta] épico: TPROJ-10998
  2. TPROJ-11089 — outra historia         [Media] épico: TPROJ-9900

Qual você quer usar? (número ou chave)
```
3. Executar a acao no ticket escolhido.

**Gatilhos do seletor:** "documenta minha estoria", "adiciona na minha historia", "coloca o criterio de aceite", qualquer acao clara sem ticket especificado.

| O usuario diz | JQL de status |
|---|---|
| (padrao) | `status = 'Em Andamento'` |
| "em testes" | `status = 'Em Testes'` |
| "backlog" | `status = Backlog` |
| "todas" | sem filtro de status |

---

## Pesquisa de Contexto

**Gatilhos:** "qual a regra de negocio de", "criterio de aceite do", "o que foi combinado sobre", "tem cenario de teste para", "busca sobre", "pesquisa no jira"

**Como executar:**
1. Extrair termos relevantes da query (remover: o, a, que, de, sobre, foi, tem, como)
2. Montar JQL:
```
project in (TPROJ,TNP,TLIGHTDIST,TLIGHTCOM,THP,TTRD,TSRV,PROJTHUN,SUP,TVAR)
AND issuetype in (Historia, Bug, Tarefa, Subtarefa, Story, Task)
AND text ~ "termo1" AND text ~ "termo2"
ORDER BY updated DESC
```
3. Chamar `searchJiraIssuesUsingJql` com campos: `summary,status,assignee,issuetype,description,comment`
4. Exibir trechos relevantes encontrados na descricao e comentarios

**Formato de resposta:**
```
TPROJ-123 — Titulo da historia [Em Andamento] (Anderson)
  Descricao: "...trecho relevante encontrado..."
  Comentario (Joao, 2026-06-15): "...decisao combinada..."
```

---

## Leitura de Issues

**Gatilhos:** "abre o TPROJ-123", "mostra o ticket", "qual o status de", "leia o ticket"

Chamar `getJiraIssue(issueKey)` e exibir:
- Resumo, tipo, status, responsavel, prioridade
- Descricao, criterios de aceite (customfield_11208), cenarios de teste (customfield_11537)
- Subtarefas (key + status)
- Ultimos comentarios (autor + data + texto)
- Parent / epic link se houver

**Para epicos:** exibir apenas campo `customfield_10902` (GMUD/link da PR). Nunca exibir Quarter, datas, garantia, handover.

---

## Criacao de Tickets

**Gatilhos:** "cria uma historia", "cria um bug", "cria uma tarefa", "cria uma subtarefa"

**Nunca criar epicos.** Se pedido, orientar a usar a skill `jira-epic-automator`.

**Fluxo antes de criar — perguntar se nao informado:**
1. Qual projeto?
2. Qual tipo? (Historia / Bug / Tarefa / Subtarefa)
3. Qual o titulo/resumo?
4. Pertence a algum epico ou historia pai?
5. Ha descricao, criterios de aceite ou cenarios de teste?

**Campos a preencher em `createJiraIssue`:**
- `summary` — titulo
- `description` — corpo principal
- `customfield_11208` — criterios de aceite
- `customfield_11537` — cenarios de teste
- `customfield_10014` — epic link (se informado)
- `parent` — para subtarefas

**Confirmar apos criar:**
```
Historia criada: TPROJ-456
Link: https://qx3prod.atlassian.net/browse/TPROJ-456
```

| Tipo | Quando usar |
|---|---|
| Historia | Funcionalidade do usuario (user story) |
| Bug | Defeito ou comportamento incorreto |
| Tarefa | Trabalho tecnico sem valor direto ao usuario |
| Subtarefa | Divisao de historia/tarefa em partes menores |

---

## Documentacao de Tickets Existentes

**Gatilhos:** "documenta o ticket", "adiciona criterio de aceite no", "escreve a descricao do", "adiciona cenario de teste no"

**Fluxo:**
1. Verificar propriedade (`atlassianUserInfo` + `getJiraIssue`)
2. Ler campos atuais: `description`, `customfield_11208`, `customfield_11537`
3. Para cada campo solicitado:
   - **Vazio:** preencher com `editJiraIssue`
   - **Ja preenchido:** informar o valor existente, nao alterar
4. Confirmar: "Adicionado: [campos]. Ja preenchidos (nao alterados): [campos]."

---

## Edicao de Campos

**Gatilhos:** "altera o campo X", "muda a prioridade para", "atualiza o resumo do", "troca o responsavel"

**Fluxo:**
1. Verificar propriedade
2. Verificar se campo esta na lista de bloqueados — rejeitar com explicacao
3. Ler valor atual com `getJiraIssue` — se preenchido, informar e nao alterar
4. Chamar `editJiraIssue(issueKey, {campo: novoValor})`

**Mapa de nomes amigaveis:**

| O usuario diz | Campo |
|---|---|
| "resumo" | summary |
| "descricao" | description |
| "criterios de aceite" / "AC" | customfield_11208 |
| "cenarios de teste" | customfield_11537 |
| "prioridade" | priority |
| "responsavel" | assignee |
| "labels" / "categorias" | labels |
| "componentes" | components |
| "sprint" | customfield_10016 |
| "time" | customfield_10600 |
| "dod" | customfield_11209 |
| "dor" | customfield_12266 |
| "criterios tecnicos" | customfield_11568 |
| "evidencias de testes" | customfield_12200 |
| "evidencias tecnicas" | customfield_12233 |

---

## Comentarios

**Gatilhos:** "comenta no ticket", "adiciona um comentario no", "registra no ticket"

Chamar `addCommentToJiraIssue(issueKey, texto)`. Comentarios sao sempre adicionados — nunca sobrescrevem.

---

## Apontamento de Horas

**Gatilhos:** "aponta Xh no TPROJ-123", "registra 2 horas no ticket", "lanca 3h 30m"

1. Verificar propriedade
2. Chamar `addWorklogToJiraIssue(issueKey, timeSpent, startedDate, comment)`
   - `timeSpent`: formato Jira — "3h", "1h 30m", "2d"
   - `startedDate`: data do trabalho (padrao: hoje)
   - `comment`: descricao opcional do trabalho realizado

---

## Transicao de Status

**Gatilhos:** "muda para Em Testes", "move para Concluido", "transiciona para"

1. Verificar propriedade
2. Chamar `getTransitionsForJiraIssue(issueKey)` para listar transicoes disponiveis
3. Identificar a transicao mais proxima do nome informado
4. Confirmar com o usuario se houver ambiguidade
5. Chamar `transitionJiraIssue(issueKey, transitionId)`

---

## Busca de Usuarios

Chamar `lookupJiraAccountId(query)` com nome ou email. Retorna `accountId` para usar em assignee.

---

## Regra de Filtragem por Tipo

**Filtrar pelo tipo exato mencionado:**

| O usuario diz | issuetype no JQL |
|---|---|
| "estorias" / "historias" | `issuetype in (Historia, Story)` |
| "bugs" | `issuetype = Bug` |
| "tarefas" | `issuetype in (Tarefa, Task)` |
| "subtarefas" | `issuetype in (Subtarefa, Sub-task)` |
| "tickets" / nao especificou | `issuetype in (Historia, Bug, Tarefa, Subtarefa, Story, Task, Sub-task)` |

---

## Como Responder

- **Pesquisa:** tabela com key, resumo, status, responsavel + trechos encontrados
- **Leitura:** resumo formatado com todos os campos visiveis
- **Criacao:** confirmacao com key gerada e link para o ticket
- **Documentacao:** confirmar campos adicionados vs ja existentes
- **Campo bloqueado:** explicar que pertence ao ciclo de vida do epico, sugerir `jira-epic-automator`
- **Sem permissao:** informar quem e o responsavel atual, nao executar a acao

---

## Exemplos de Uso

| O usuario diz | Acao |
|---|---|
| "qual a regra de negocio do campo CCEE?" | `searchJiraIssuesUsingJql` com termos "regra CCEE" |
| "abre o TPROJ-123" | `getJiraIssue("TPROJ-123")` |
| "quais minhas estorias em andamento?" | `searchJiraIssuesUsingJql` com `assignee = currentUser()` |
| "cria uma historia no TPROJ para o epico TPROJ-100" | perguntar resumo + contexto → `createJiraIssue` |
| "cria um bug: tela de fatura quebrando no TLIGHTDIST" | `createJiraIssue("TLIGHTDIST", "Tela de fatura quebrando", "Bug")` |
| "adiciona criterio de aceite no TPROJ-123" | verificar ownership → `editJiraIssue` com customfield_11208 |
| "comenta no TPROJ-123: alinhado com o time" | `addCommentToJiraIssue("TPROJ-123", "alinhado com o time")` |
| "aponta 3h no TPROJ-456" | verificar ownership → `addWorklogToJiraIssue("TPROJ-456", "3h")` |
| "move o TPROJ-456 para Em Testes" | `getTransitionsForJiraIssue` → `transitionJiraIssue` |
| "qual o link da PR do epico TPROJ-100?" | `getJiraIssue("TPROJ-100")` → campo customfield_10902 |

---

## Tratamento de Erros

- **Campo ja preenchido:** informa valor atual, nao altera nada
- **Criar epico:** bloqueia e orienta a usar `jira-epic-automator`
- **Campo bloqueado de epico:** informa que e campo de ciclo de vida, nao disponivel
- **Issue nao encontrado:** pedir confirmacao da chave com o usuario
- **Usuario sem permissao (nao e assignee):** informar quem e o responsavel atual, nao executar
- **Conector Atlassian indisponivel:** orientar o usuario a habilitar o plugin Atlassian no Claude
