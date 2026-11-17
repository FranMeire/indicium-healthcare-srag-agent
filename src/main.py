import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from src.agent.graph import build_srag_agent
from src.agent.guardrails import (
    apply_output_guardrails,
    log_audit_event,
    validate_input_query,
)

load_dotenv()


def run_pipeline():
    user_prompt = (
        "Gere o relatório epidemiológico completo de SRAG com as 4 métricas principais, "
        "os gráficos de 30 dias e 12 meses e a análise contextualizada com notícias atuais."
    )

    print("1. Validando Guardrails de entrada...")
    safe_prompt = validate_input_query(user_prompt)
    log_audit_event("INPUT_VALIDATED", {"prompt": safe_prompt})

    print("2. Executando Agente Orquestrador LangGraph (SQL + Gráficos + Notícias)...")
    agent = build_srag_agent()
    response = agent.invoke({"messages": [HumanMessage(content=safe_prompt)]})

    for msg in response["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                log_audit_event("TOOL_CALL", {"tool": tc["name"], "args": tc["args"]})

    raw_report = response["messages"][-1].content
    final_report = apply_output_guardrails(raw_report)

    os.makedirs("outputs", exist_ok=True)
    report_path = "outputs/relatorio_srag.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_report)

    log_audit_event("REPORT_GENERATED", {"output_path": report_path})
    print(f"3. Sucesso! Relatório salvo em: {report_path}")
    print("   Logs de auditoria salvos em: outputs/audit_log.jsonl")


if __name__ == "__main__":
    run_pipeline()
