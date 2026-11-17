import json
import os
import re
from datetime import datetime

AUDIT_LOG_PATH = "outputs/audit_log.jsonl"


def validate_input_query(user_query: str) -> str:
    """Guardrail de entrada: bloqueia prompt injection ou solicitação de dados sensíveis."""
    forbidden_patterns = [
        r"ignore\s+previous\s+instructions",
        r"drop\s+table",
        r"delete\s+from",
        r"cpf",
        r"nome\s+do\s+paciente",
    ]
    for pattern in forbidden_patterns:
        if re.search(pattern, user_query, re.IGNORECASE):
            raise ValueError(
                "Solicitação bloqueada pelos Guardrails de Segurança/LGPD."
            )
    return user_query


def apply_output_guardrails(report_text: str) -> str:
    """Guardrail de saída: adiciona aviso obrigatório de governança clínica."""
    disclaimer = (
        "\n\n---\n"
        "**Aviso de Governança e Uso Clínico (Guardrail):** Este relatório foi gerado automaticamente "
        "por Inteligência Artificial a partir de microdados públicos anonimizados do Open DATASUS (SIVEP-Gripe) "
        "e notícias recentes. Os indicadores têm caráter estritamente informativo e epidemiológico, "
        "não substituindo protocolos médicos ou decisões clínicas individuais."
    )
    if "Aviso de Governança" not in report_text:
        report_text += disclaimer
    return report_text


def log_audit_event(step: str, details: dict) -> None:
    """Registra decisões e chamadas do agente em arquivo JSONL auditável."""
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step,
        "details": details,
    }
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
