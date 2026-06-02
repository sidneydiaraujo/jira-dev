"""
Jira Dev — Criacao e documentacao de tickets para desenvolvedores.

Permissoes:
  - LEITURA: qualquer issue (exceto campos de ciclo de vida dos epicos)
  - ESCRITA: historias, bugs, tarefas, subtarefas — nunca sobrescreve campos ja preenchidos
  - EPICOS: apenas leitura do campo GMUD (link da PR); pode criar filhos de epico

Campos de epico BLOQUEADOS (nunca lidos nem escritos por esta skill):
  Quarter, Start Date, Data Limite, Data de Publicacao, Data de Garantia,
  Ciclos de Garantia, Responsavel Handover, Fix Versions, status do epico.
"""
import os
import re
import sys
import json
import requests
from datetime import datetime, timezone
from pathlib import Path

JIRA_BASE = "https://qx3prod.atlassian.net/rest/api/3"
PROJECTS  = ["TPROJ", "TNP", "TLIGHTDIST", "TLIGHTCOM", "THP",
             "TTRD", "TSRV", "PROJTHUN", "SUP", "TVAR"]

# Campos dedicados para documentacao de tickets
_FIELD_AC       = "customfield_11208"   # Criterios de Aceitacao
_FIELD_CENARIOS = "customfield_11537"   # Cenarios de Testes

# Campos de ciclo de vida de epicos — NUNCA acessar por esta skill
_EPIC_BLOCKED_FIELDS = {
    "customfield_11450",   # Quarter
    "customfield_11201",   # Start Date
    "duedate",             # Data Limite
    "customfield_11336",   # Data de Publicacao
    "customfield_12132",   # Data de Garantia
    "customfield_12131",   # Ciclos de Garantia
    "customfield_12167",   # Responsavel Handover
    "fixVersions",
}

# Campo GMUD (unico campo de epico permitido para leitura)
_GMUD_FIELD = "customfield_10902"

# Nomes de campos bloqueados para mensagens de erro
_EPIC_BLOCKED_NAMES = [
    "Quarter", "Start Date", "Data Limite", "Data de Publicacao",
    "Data de Garantia", "Ciclos de Garantia", "Responsavel Handover",
    "Fix Versions", "status",
]

# Campos que NUNCA podem ser alterados por esta skill (em qualquer issue)
_WRITE_BLOCKED_FIELDS = {
    "parent",               # Pai — estrutura do backlog
    "customfield_12368",    # Complexidade
    "customfield_12436",    # IA
    "issuetype",            # Tipo de item — alteracao estrutural
    "fixVersions",          # Versoes corrigidas — gerenciado pelo epic automator
} | _EPIC_BLOCKED_FIELDS

_WRITE_BLOCKED_NAMES = {
    "parent":             "Pai (campo estrutural — nao alteravel)",
    "customfield_12368":  "Complexidade (campo bloqueado por politica)",
    "customfield_12436":  "IA (campo bloqueado por politica)",
    "issuetype":          "Tipo de item (alteracao estrutural nao permitida)",
    "fixVersions":        "Versoes corrigidas (gerenciado pelo jira-epic-automator)",
}

# Mapa de nomes amigaveis para IDs de campos editaveis
FIELD_ALIASES = {
    "resumo":                    "summary",
    "summary":                   "summary",
    "descricao":                 "description",
    "description":               "description",
    "criterios de aceitacao":    _FIELD_AC,
    "criterios de aceite":       _FIELD_AC,
    "ac":                        _FIELD_AC,
    "cenarios de teste":         _FIELD_CENARIOS,
    "cenarios de testes":        _FIELD_CENARIOS,
    "cenarios":                  _FIELD_CENARIOS,
    "prioridade":                "priority",
    "priority":                  "priority",
    "responsavel":               "assignee",
    "assignee":                  "assignee",
    "categorias":                "labels",
    "labels":                    "labels",
    "componentes":               "components",
    "components":                "components",
    "data limite":               "duedate",
    "duedate":                   "duedate",
    "data de inicio":            "customfield_11201",
    "sprint":                    "customfield_10016",
    "time":                      "customfield_10600",
    "tipo de erro":              "customfield_11429",
    "ambiente":                  "environment",
    "dod":                       "customfield_11209",
    "definition of done":        "customfield_11209",
    "dor":                       "customfield_12266",
    "definition of ready":       "customfield_12266",
    "criterios tecnicos":        "customfield_11568",
    "evidencias de testes":      "customfield_12200",
    "evidencias tecnicas":       "customfield_12233",
}


# ---------------------------------------------------------------------------
# Helpers de API
# ---------------------------------------------------------------------------

def _auth():
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not email or not token:
        raise EnvironmentError(
            "JIRA_EMAIL e JIRA_API_TOKEN sao obrigatorios. Configure via /update-config."
        )
    return (email, token)


def _headers():
    return {"Accept": "application/json", "Content-Type": "application/json"}


def _get(path, params=None):
    r = requests.get(f"{JIRA_BASE}{path}", auth=_auth(), headers=_headers(), params=params)
    r.raise_for_status()
    return r.json()


def _post(path, body):
    r = requests.post(f"{JIRA_BASE}{path}", auth=_auth(), headers=_headers(), json=body)
    r.raise_for_status()
    return r.json() if r.content else {}


def _put(path, body):
    r = requests.put(f"{JIRA_BASE}{path}", auth=_auth(), headers=_headers(), json=body)
    r.raise_for_status()
    return r.json() if r.content else {}


def _search(jql, fields, max_results=50):
    results, next_token = [], None
    fields_list = fields if isinstance(fields, list) else fields.split(",")
    while True:
        payload = {"jql": jql, "fields": fields_list,
                   "maxResults": min(100, max_results)}
        if next_token:
            payload["nextPageToken"] = next_token
        data = _post("/search/jql", payload)
        batch = data.get("issues", [])
        results.extend(batch)
        next_token = data.get("nextPageToken")
        if not next_token or len(results) >= max_results or len(batch) < 100:
            break
    return results


def _is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, (int, float)) and value == 0:
        return True
    if isinstance(value, (list, dict)) and not value:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


# ---------------------------------------------------------------------------
# ADF (Atlassian Document Format)
# ---------------------------------------------------------------------------

def _adf_to_text(node) -> str:
    """Extrai texto plano de um no ADF recursivamente."""
    if not node:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        t = node.get("type", "")
        text = node.get("text", "")
        children = node.get("content", [])
        parts = [text] if text else []
        for child in children:
            parts.append(_adf_to_text(child))
        separator = "\n" if t in ("paragraph", "heading", "listItem", "bulletList",
                                   "orderedList", "blockquote", "codeBlock", "rule",
                                   "tableRow", "tableCell") else ""
        return separator.join(p for p in parts if p)
    return ""


def _text_to_adf(text: str) -> dict:
    """Converte texto plano em ADF simples (paragrafos separados por linha em branco)."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    content = []
    for para in paragraphs:
        lines = para.split("\n")
        inline = []
        for i, line in enumerate(lines):
            if i > 0:
                inline.append({"type": "hardBreak"})
            inline.append({"type": "text", "text": line})
        content.append({
            "type": "paragraph",
            "content": inline,
        })
    if not content:
        content = [{"type": "paragraph", "content": []}]
    return {"type": "doc", "version": 1, "content": content}


def _build_adf_section(title: str, body: str) -> list:
    """Retorna lista de nos ADF: cabecalho + paragrafo."""
    return [
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": title}],
        },
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": body}],
        },
    ]


def _build_full_description(description: str = "",
                             acceptance_criteria: str = "",
                             test_scenarios: str = "") -> dict:
    """Monta ADF estruturado com descricao, criterios de aceite e cenarios de teste."""
    content = []

    if description:
        content.extend(_build_adf_section("Descricao", description))

    if acceptance_criteria:
        content.extend(_build_adf_section("Criterios de Aceite", acceptance_criteria))

    if test_scenarios:
        content.extend(_build_adf_section("Cenarios de Teste", test_scenarios))

    if not content:
        content = [{"type": "paragraph", "content": []}]

    return {"type": "doc", "version": 1, "content": content}


# ---------------------------------------------------------------------------
# Pesquisa de conteudo (mesma logica do jira-analytics Module 5)
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da",
    "dos", "das", "em", "no", "na", "nos", "nas", "por", "para", "com",
    "que", "e", "ou", "mas", "se", "ao", "ate", "sob", "sobre", "entre",
    "como", "quando", "onde", "qual", "quais", "isso", "isto", "aquilo",
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "or",
    "is", "was", "are", "were", "be", "been", "being", "have", "has",
    "what", "which", "who", "how", "when", "where",
    "me", "mostra", "busca", "pesquisa", "encontra", "procura",
    "nos", "ultimos", "ultima", "ultimo", "dias", "semana", "mes",
    "foi", "foram", "esta", "estao", "tem", "ha", "tinha",
}


def _parse_natural_query(query: str) -> dict:
    text = query.strip()
    days = None
    # Detectar filtro de data
    m = re.search(r"ultimos?\s+(\d+)\s+dias?", text, re.IGNORECASE)
    if m:
        days = int(m.group(1))
    elif re.search(r"esta\s+semana|essa\s+semana", text, re.IGNORECASE):
        days = 7
    elif re.search(r"este\s+mes|esse\s+mes", text, re.IGNORECASE):
        days = 30

    # Detectar campo preferido
    field_hint = None
    if re.search(r"coment[aá]rio|combinado|decidido|alinhado", text, re.IGNORECASE):
        field_hint = "comment"
    elif re.search(r"crit[eé]rio|aceite|cen[aá]rio|bdd|gherkin|descri", text, re.IGNORECASE):
        field_hint = "description"

    # Extrair termos (remove stopwords e pontuacao)
    tokens = re.findall(r'"[^"]+"|\w+', text)
    terms = []
    for t in tokens:
        if t.startswith('"'):
            terms.append(t[1:-1])
        elif len(t) > 2 and t.lower() not in _STOPWORDS:
            terms.append(t)

    return {"terms": terms, "days": days, "field_hint": field_hint}


def _extract_snippet(text: str, terms: list, window: int = 200) -> str:
    if not text:
        return ""
    lower = text.lower()
    best_pos = len(text)
    for t in terms:
        pos = lower.find(t.lower())
        if 0 <= pos < best_pos:
            best_pos = pos
    start = max(0, best_pos - 60)
    end = min(len(text), best_pos + window)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def search_content(query: str, project_keys=None, days: int = None,
                   max_results: int = 20) -> dict:
    """Pesquisa em linguagem natural dentro de descricoes, criterios de aceite e comentarios.

    Nao retorna campos de ciclo de vida de epicos.
    """
    projects = project_keys or PROJECTS
    parsed = _parse_natural_query(query)
    terms = parsed["terms"]
    if not terms:
        return {"erro": "Nao foi possivel extrair termos de busca da query."}

    effective_days = days or parsed.get("days")
    project_filter = " OR ".join(f"project = {p}" for p in projects)
    term_filters = []
    for t in terms[:2]:
        if " " in t:
            term_filters.append(f'text ~ \\"{t}\\"')
        else:
            term_filters.append(f'text ~ "{t}"')
    term_jql = " AND ".join(term_filters) if term_filters else f'text ~ "{terms[0]}"'

    type_filter = 'issuetype in (Historia, Bug, Tarefa, Subtarefa, Story, Task, Sub-task, Impedimento)'
    jql = f"({project_filter}) AND {type_filter} AND ({term_jql})"

    if effective_days:
        jql += f" AND updated >= -{effective_days}d"

    jql += " ORDER BY updated DESC"

    issues = _search(jql, "summary,status,assignee,issuetype,created,updated,description,comment",
                     max_results=max_results)

    results = []
    for issue in issues:
        f = issue["fields"]
        desc_text = _adf_to_text(f.get("description"))
        raw_comments = (f.get("comment") or {}).get("comments", [])
        comments = [
            {
                "author": (c.get("author") or {}).get("displayName", "?"),
                "date": c.get("created", "")[:16].replace("T", " "),
                "text": _adf_to_text(c.get("body")),
            }
            for c in raw_comments
        ]

        matches = []
        if desc_text and any(t.lower() in desc_text.lower() for t in terms):
            matches.append({
                "campo": "descricao",
                "trecho": _extract_snippet(desc_text, terms),
            })
        for c in comments:
            if any(t.lower() in c["text"].lower() for t in terms):
                matches.append({
                    "campo": f'comentario — {c["author"]} ({c["date"]})',
                    "trecho": _extract_snippet(c["text"], terms),
                })
        if not matches:
            matches.append({"campo": "resumo", "trecho": f.get("summary", "")})

        results.append({
            "key": issue["key"],
            "resumo": f.get("summary", ""),
            "tipo": (f.get("issuetype") or {}).get("name", ""),
            "status": (f.get("status") or {}).get("name", ""),
            "responsavel": (f.get("assignee") or {}).get("displayName", "—"),
            "criado": f.get("created", "")[:10],
            "atualizado": f.get("updated", "")[:10],
            "total_comentarios": (f.get("comment") or {}).get("total", len(comments)),
            "matches": matches,
        })

    return {
        "query": query,
        "termos_usados": terms,
        "jql_gerado": jql,
        "total": len(results),
        "resultados": results,
    }


# ---------------------------------------------------------------------------
# Leitura de issues (com filtro de campos de epico)
# ---------------------------------------------------------------------------

def get_issue(issue_key: str) -> dict:
    """Retorna dados de um issue. Para epicos, omite campos de ciclo de vida."""
    data = _get(f"/issue/{issue_key}",
                params={"fields": "summary,description,status,assignee,issuetype,"
                                  "priority,created,updated,comment,subtasks,"
                                  "parent,labels,components,fixVersions,"
                                  f"customfield_10014,{_GMUD_FIELD}"})
    f = data["fields"]
    issue_type = (f.get("issuetype") or {}).get("name", "").lower()

    result = {
        "key": data["key"],
        "tipo": (f.get("issuetype") or {}).get("name", ""),
        "resumo": f.get("summary", ""),
        "status": (f.get("status") or {}).get("name", ""),
        "responsavel": (f.get("assignee") or {}).get("displayName", "—"),
        "prioridade": (f.get("priority") or {}).get("name", ""),
        "criado": f.get("created", "")[:10],
        "atualizado": f.get("updated", "")[:10],
        "descricao": _adf_to_text(f.get("description")),
        "labels": f.get("labels", []),
        "subtarefas": [
            {"key": s["key"], "resumo": s["fields"]["summary"],
             "status": s["fields"]["status"]["name"]}
            for s in f.get("subtasks", [])
        ],
    }

    # Parent / Epic link
    parent = f.get("parent")
    if parent:
        result["parent"] = {
            "key": parent["key"],
            "resumo": parent["fields"]["summary"],
            "tipo": parent["fields"]["issuetype"]["name"],
        }

    epic_link = f.get("customfield_10014")
    if epic_link and not parent:
        result["epic_link"] = epic_link

    # Para epicos: mostrar apenas GMUD
    if "epic" in issue_type:
        gmud_val = f.get(_GMUD_FIELD)
        result["gmud"] = gmud_val if gmud_val else None
        result["_aviso"] = (
            "Epico: campos de ciclo de vida (Quarter, datas, garantia, handover) "
            "nao sao exibidos por esta skill."
        )

    # Comentarios
    raw_comments = (f.get("comment") or {}).get("comments", [])
    result["comentarios"] = [
        {
            "autor": (c.get("author") or {}).get("displayName", "?"),
            "data": c.get("created", "")[:16].replace("T", " "),
            "texto": _adf_to_text(c.get("body")),
        }
        for c in raw_comments
    ]

    return result


def get_epic_gmud(epic_key: str) -> dict:
    """Retorna apenas o campo GMUD (link da PR) de um epico."""
    data = _get(f"/issue/{epic_key}",
                params={"fields": f"summary,issuetype,{_GMUD_FIELD}"})
    f = data["fields"]
    issue_type = (f.get("issuetype") or {}).get("name", "").lower()
    if "epic" not in issue_type:
        return {"erro": f"{epic_key} nao e um epico (tipo: {f.get('issuetype', {}).get('name')})"}
    return {
        "key": epic_key,
        "resumo": f.get("summary", ""),
        "gmud": f.get(_GMUD_FIELD),
    }


# ---------------------------------------------------------------------------
# Criacao de tickets
# ---------------------------------------------------------------------------

def create_issue(project_key: str,
                 summary: str,
                 issuetype: str,
                 description: str = "",
                 acceptance_criteria: str = "",
                 test_scenarios: str = "",
                 epic_link: str = None,
                 parent_key: str = None,
                 assignee_account_id: str = None,
                 labels: list = None,
                 priority: str = None) -> dict:
    """Cria um novo issue (Historia, Bug, Tarefa, Subtarefa).

    Nunca cria epicos — use a jira-epic-automator para isso.
    Nunca sobrescreve issues existentes — esta funcao apenas cria novos.

    Args:
        project_key: chave do projeto (ex: "TPROJ")
        summary: titulo do ticket
        issuetype: "Historia", "Bug", "Tarefa", "Subtarefa" (ou equivalente em ingles)
        description: corpo principal da descricao
        acceptance_criteria: criterios de aceite (formatado como secao separada)
        test_scenarios: cenarios de teste BDD/Gherkin ou descritivos
        epic_link: chave do epico pai (ex: "TPROJ-100") — campo customfield_10014
        parent_key: chave do item pai para subtarefas
        assignee_account_id: accountId Jira do responsavel
        labels: lista de labels
        priority: nome da prioridade (ex: "Alta", "Media", "Baixa")
    """
    issuetype_lower = issuetype.lower()
    if "epic" in issuetype_lower or "epico" in issuetype_lower:
        return {
            "erro": "Esta skill nao cria epicos. Use a jira-epic-automator para gestao de epicos."
        }

    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": issuetype},
    }

    if description:
        fields["description"] = _text_to_adf(description)
    if acceptance_criteria:
        fields[_FIELD_AC] = _text_to_adf(acceptance_criteria)
    if test_scenarios:
        fields[_FIELD_CENARIOS] = _text_to_adf(test_scenarios)

    if epic_link:
        fields["customfield_10014"] = epic_link

    if parent_key:
        fields["parent"] = {"key": parent_key}

    if assignee_account_id:
        fields["assignee"] = {"accountId": assignee_account_id}

    if labels:
        fields["labels"] = labels

    if priority:
        fields["priority"] = {"name": priority}

    result = _post("/issue", {"fields": fields})
    return {
        "ok": True,
        "key": result.get("key"),
        "url": f"https://qx3prod.atlassian.net/browse/{result.get('key')}",
        "summary": summary,
        "tipo": issuetype,
        "projeto": project_key,
    }


# ---------------------------------------------------------------------------
# Atualizacao segura de campos
# ---------------------------------------------------------------------------

def update_field(issue_key: str, field: str, value, force: bool = False) -> dict:
    """Atualiza um campo de um issue, somente se estiver vazio.

    Campos de ciclo de vida de epicos sao sempre bloqueados.
    Para atualizar campos ja preenchidos, use force=True (requer confirmacao explicita do usuario).
    """
    if field in _EPIC_BLOCKED_FIELDS:
        return {
            "erro": f"Campo '{field}' e de ciclo de vida de epico e nao pode ser alterado por esta skill.",
            "campos_bloqueados": _EPIC_BLOCKED_NAMES,
        }

    data = _get(f"/issue/{issue_key}", params={"fields": field})
    current = data["fields"].get(field)

    if not _is_empty(current) and not force:
        return {
            "aviso": f"Campo '{field}' ja esta preenchido.",
            "valor_atual": current,
            "acao": "Nenhuma alteracao feita. Use force=True para sobrescrever.",
        }

    _put(f"/issue/{issue_key}", {"fields": {field: value}})
    return {
        "ok": True,
        "key": issue_key,
        "campo": field,
        "valor_anterior": current,
        "novo_valor": value,
    }


def update_description(issue_key: str,
                        description: str = None,
                        acceptance_criteria: str = None,
                        test_scenarios: str = None) -> dict:
    """Atualiza os campos de documentacao de um issue.

    - description       → campo 'description' (corpo principal)
    - acceptance_criteria → campo customfield_11208 (Criterios de Aceitacao)
    - test_scenarios    → campo customfield_11537 (Cenarios de Testes)

    Nunca sobrescreve campos ja preenchidos.
    """
    fields_to_read = f"description,{_FIELD_AC},{_FIELD_CENARIOS},issuetype,summary"
    data = _get(f"/issue/{issue_key}", params={"fields": fields_to_read})
    f = data["fields"]

    issue_type = (f.get("issuetype") or {}).get("name", "").lower()
    if "epic" in issue_type:
        return {"erro": "Nao e permitido editar campos de epicos por esta skill."}

    updates = {}
    skipped = {}
    saved = []

    # Campo descricao
    if description:
        current = _adf_to_text(f.get("description") or {})
        if _is_empty(current):
            updates["description"] = _text_to_adf(description)
            saved.append("Descricao")
        else:
            skipped["Descricao"] = current[:120]

    # Campo Criterios de Aceitacao
    if acceptance_criteria:
        current = _adf_to_text(f.get(_FIELD_AC) or {})
        if _is_empty(current):
            updates[_FIELD_AC] = _text_to_adf(acceptance_criteria)
            saved.append("Criterios de Aceitacao")
        else:
            skipped["Criterios de Aceitacao"] = current[:120]

    # Campo Cenarios de Testes
    if test_scenarios:
        current = _adf_to_text(f.get(_FIELD_CENARIOS) or {})
        if _is_empty(current):
            updates[_FIELD_CENARIOS] = _text_to_adf(test_scenarios)
            saved.append("Cenarios de Testes")
        else:
            skipped["Cenarios de Testes"] = current[:120]

    if not updates:
        return {
            "aviso": "Todos os campos solicitados ja estao preenchidos.",
            "ja_preenchidos": skipped,
            "acao": "Nenhuma alteracao feita.",
        }

    _put(f"/issue/{issue_key}", {"fields": updates})
    return {
        "ok": True,
        "key": issue_key,
        "salvos": saved,
        "ignorados_ja_preenchidos": list(skipped.keys()),
    }


# ---------------------------------------------------------------------------
# Seguranca — verificacao de propriedade antes de qualquer escrita
# ---------------------------------------------------------------------------

def _get_current_user() -> dict:
    """Retorna accountId e displayName do usuario autenticado."""
    data = _get("/myself")
    return {"accountId": data.get("accountId"), "displayName": data.get("displayName", "")}


def _verify_ownership(issue_key: str) -> dict:
    """Verifica se o usuario atual e o responsavel (assignee) do issue.

    Retorna dict com 'ok': True se autorizado, ou 'erro' se nao for.
    Bloqueia epicos por padrao — esta skill nao escreve em epicos.
    """
    data = _get(f"/issue/{issue_key}",
                params={"fields": "assignee,issuetype,summary,status"})
    f = data["fields"]

    issue_type = (f.get("issuetype") or {}).get("name", "").lower()
    if "epic" in issue_type:
        return {
            "ok": False,
            "erro": f"{issue_key} e um epico. Esta skill nao escreve em epicos.",
        }

    assignee = f.get("assignee") or {}
    assignee_id = assignee.get("accountId")
    assignee_name = assignee.get("displayName", "nao atribuido")

    me = _get_current_user()

    if not assignee_id:
        return {
            "ok": False,
            "erro": f"{issue_key} nao tem responsavel atribuido. Atribua-se primeiro.",
        }

    if assignee_id != me["accountId"]:
        return {
            "ok": False,
            "erro": (
                f"Voce nao e o responsavel por {issue_key}. "
                f"Responsavel atual: {assignee_name}. "
                "Esta skill so permite editar issues sob sua responsabilidade."
            ),
            "responsavel_atual": assignee_name,
            "voce": me["displayName"],
        }

    return {
        "ok": True,
        "key": issue_key,
        "responsavel": assignee_name,
        "tipo": (f.get("issuetype") or {}).get("name", ""),
        "status": (f.get("status") or {}).get("name", ""),
        "resumo": f.get("summary", ""),
    }


def edit_field(issue_key: str, field: str, value) -> dict:
    """Edita um campo de um issue, com verificacao de propriedade e lista de campos bloqueados.

    Regras de seguranca aplicadas:
      1. Usuario deve ser o responsavel (assignee) do issue
      2. Issue nao pode ser um epico
      3. Campo nao pode estar na lista de bloqueados (complexidade, IA, pai, tipo, etc.)
      4. Campos de texto sao convertidos para ADF automaticamente

    Args:
        issue_key: chave do issue (ex: "TPROJ-11150")
        field:     nome amigavel ou ID do campo (ex: "prioridade", "summary", "customfield_11208")
        value:     novo valor. Para campos de texto, passe string. Para outros, passe o valor direto.
    """
    # Resolver alias para ID de campo
    field_id = FIELD_ALIASES.get(field.lower().strip(), field)

    # Verificar se campo e bloqueado
    if field_id in _WRITE_BLOCKED_FIELDS:
        nome_bloqueado = _WRITE_BLOCKED_NAMES.get(field_id, field_id)
        return {
            "ok": False,
            "erro": f"Campo '{nome_bloqueado}' nao pode ser alterado por esta skill.",
            "motivo": "Campo bloqueado por politica de seguranca.",
        }

    # Verificar propriedade do issue
    ownership = _verify_ownership(issue_key)
    if not ownership["ok"]:
        return ownership

    # Campos que recebem ADF (texto rico)
    adf_fields = {
        "description", _FIELD_AC, _FIELD_CENARIOS,
        "customfield_11209",   # DoD
        "customfield_12266",   # DoR
        "customfield_11568",   # Criterios Tecnicos
        "customfield_12233",   # Evidencias Tecnicas
        "customfield_12200",   # Evidencias de Testes
        "environment",
    }

    # Montar payload conforme tipo do campo
    if field_id in adf_fields and isinstance(value, str):
        payload = _text_to_adf(value)
    elif field_id == "assignee":
        payload = {"accountId": value} if isinstance(value, str) else value
    elif field_id == "priority":
        _priority_map = {
            "muito alta": "Highest", "highest": "Highest",
            "alta":       "High",    "high":    "High",
            "media":      "Medium",  "medium":  "Medium",
            "baixa":      "Low",     "low":     "Low",
            "muito baixa":"Lowest",  "lowest":  "Lowest",
        }
        name = _priority_map.get(value.lower().strip(), value) if isinstance(value, str) else value
        payload = {"name": name} if isinstance(name, str) else name
    elif field_id == "labels":
        payload = value if isinstance(value, list) else [value]
    else:
        payload = value

    _put(f"/issue/{issue_key}", {"fields": {field_id: payload}})
    return {
        "ok": True,
        "key": issue_key,
        "campo": field_id,
        "nome_campo": field,
        "novo_valor": str(value)[:120],
    }


def clear_field(issue_key: str, field: str) -> dict:
    """Apaga o conteudo de um campo da sua propria estoria.

    Permitido apenas se:
      - Voce for o responsavel (assignee) do issue
      - O campo nao estiver na lista de bloqueados
      - O campo nao for 'summary' (resumo nao pode ficar vazio no Jira)

    Campos de texto (description, AC, cenarios, etc.) sao zerados com ADF vazio.
    Campos simples (priority, labels, etc.) recebem null.
    """
    field_id = FIELD_ALIASES.get(field.lower().strip(), field)

    if field_id in _WRITE_BLOCKED_FIELDS:
        nome_bloqueado = _WRITE_BLOCKED_NAMES.get(field_id, field_id)
        return {
            "ok": False,
            "erro": f"Campo '{nome_bloqueado}' nao pode ser alterado por esta skill.",
        }

    if field_id == "summary":
        return {
            "ok": False,
            "erro": "O campo 'resumo' nao pode ser apagado — o Jira exige que esteja preenchido.",
        }

    ownership = _verify_ownership(issue_key)
    if not ownership["ok"]:
        return ownership

    # Campos ADF: zerar com documento vazio
    adf_fields = {
        "description", _FIELD_AC, _FIELD_CENARIOS,
        "customfield_11209", "customfield_12266", "customfield_11568",
        "customfield_12233", "customfield_12200", "environment",
    }

    if field_id in adf_fields:
        payload = {"type": "doc", "version": 1, "content": []}
    else:
        payload = None

    _put(f"/issue/{issue_key}", {"fields": {field_id: payload}})
    return {
        "ok": True,
        "key": issue_key,
        "campo_apagado": field,
        "field_id": field_id,
    }


# ---------------------------------------------------------------------------
# Comentarios
# ---------------------------------------------------------------------------

def add_comment(issue_key: str, text: str) -> dict:
    """Adiciona comentario a um issue. Comentarios nunca sobrescrevem — sempre sao adicionados."""
    adf_body = _text_to_adf(text)
    result = _post(f"/issue/{issue_key}/comment", {"body": adf_body})
    return {
        "ok": True,
        "key": issue_key,
        "comment_id": result.get("id"),
        "autor": (result.get("author") or {}).get("displayName", ""),
        "criado": result.get("created", "")[:16].replace("T", " "),
    }


def add_worklog(issue_key: str, time_spent: str,
                date: str = None, comment: str = None) -> dict:
    """Registra apontamento de horas (worklog) em um issue.

    Args:
        issue_key:  chave do issue (ex: "TPROJ-11157")
        time_spent: tempo gasto no formato Jira (ex: "3h", "1h 30m", "2d")
        date:       data do apontamento em "YYYY-MM-DD" (padrao: hoje)
        comment:    observacao opcional sobre o trabalho realizado
    """
    if date:
        started = f"{date}T09:00:00.000+0000"
    else:
        started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000+0000")

    body = {"timeSpent": time_spent, "started": started}
    if comment:
        body["comment"] = _text_to_adf(comment)

    result = _post(f"/issue/{issue_key}/worklog", body)
    return {
        "ok": True,
        "key": issue_key,
        "worklog_id": result.get("id"),
        "tempo_apontado": result.get("timeSpent"),
        "data": (result.get("started") or "")[:10],
    }


def transition_issue(issue_key: str, status_name: str) -> dict:
    """Transiciona um issue para o status informado por nome.

    Exemplos de status: 'Em Andamento', 'Em Testes', 'Concluido', 'Backlog', 'Bloqueado'
    """
    transitions = _get(f"/issue/{issue_key}/transitions").get("transitions", [])
    match = next(
        (t for t in transitions if status_name.lower() in t["name"].lower()), None
    )
    if not match:
        available = [t["name"] for t in transitions]
        return {"erro": f"Status '{status_name}' nao encontrado.", "disponiveis": available}

    _post(f"/issue/{issue_key}/transitions", {"transition": {"id": match["id"]}})
    return {"ok": True, "key": issue_key, "novo_status": match["name"]}


# ---------------------------------------------------------------------------
# Busca de usuarios
# ---------------------------------------------------------------------------

def list_my_stories(status: str = "em andamento") -> dict:
    """Lista as estorias do usuario autenticado filtradas por status.

    Args:
        status: "em andamento" (padrao), "backlog", "em testes", "todas"

    Retorna lista numerada pronta para o usuario escolher qual ticket quer editar.
    """
    me = _get_current_user()

    status_map = {
        "em andamento":  '"Em andamento"',
        "andamento":     '"Em andamento"',
        "backlog":       "Backlog",
        "em testes":     '"Em Testes"',
        "testes":        '"Em Testes"',
        "todas":         None,
    }

    status_jql = status_map.get(status.lower().strip(), '"Em andamento"')

    jql = (
        f'assignee = "{me["accountId"]}" '
        f'AND issuetype in (Historia, Story) '
    )
    if status_jql:
        jql += f'AND status = {status_jql} '
    jql += "ORDER BY updated DESC"

    issues = _search(
        jql,
        "summary,status,priority,parent,customfield_10014,updated",
        max_results=20,
    )

    items = []
    for i, issue in enumerate(issues, start=1):
        f = issue["fields"]
        parent = (f.get("parent") or {}).get("key", "")
        epic = f.get("customfield_10014") or ""
        items.append({
            "numero":    i,
            "key":       issue["key"],
            "resumo":    f.get("summary", ""),
            "status":    (f.get("status") or {}).get("name", ""),
            "prioridade":(f.get("priority") or {}).get("name", ""),
            "epico":     epic or parent,
            "atualizado": f.get("updated", "")[:10],
        })

    return {
        "usuario": me["displayName"],
        "filtro_status": status,
        "total": len(items),
        "estorias": items,
    }


def find_user(query: str) -> list:
    """Busca usuarios por nome ou email para obter o accountId."""
    data = _get("/user/search", params={"query": query, "maxResults": 5})
    return [
        {
            "accountId": u["accountId"],
            "nome": u.get("displayName", ""),
            "email": u.get("emailAddress", ""),
        }
        for u in data
    ]


# ---------------------------------------------------------------------------
# Listagem de tipos de issue e projetos
# ---------------------------------------------------------------------------

def get_issue_types(project_key: str) -> list:
    """Lista tipos de issue disponiveis em um projeto."""
    data = _get(f"/project/{project_key}/issuetypes")
    return [
        {"id": t["id"], "nome": t["name"], "subtarefa": t.get("subtask", False)}
        for t in data
        if "epic" not in t["name"].lower()
    ]


def get_transitions(issue_key: str) -> list:
    """Lista transicoes de status disponiveis para um issue."""
    data = _get(f"/issue/{issue_key}/transitions")
    return [
        {"id": t["id"], "nome": t["name"]}
        for t in data.get("transitions", [])
    ]
