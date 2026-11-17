import os
from langchain_core.tools import tool
from tavily import TavilyClient


@tool
def search_srag_news(query: str = "Síndrome Respiratória Aguda Grave SRAG Brasil Ministério da Saúde") -> str:
    """
    Busca notícias recentes sobre Síndrome Respiratória Aguda Grave (SRAG) no Brasil.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or "sua_chave" in api_key or "cole-sua-chave" in api_key:
        return "Aviso: TAVILY_API_KEY não configurada no .env."

    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        search_depth="advanced",
        topic="news",
        max_results=5,
    )

    articles = []
    for item in response.get("results", []):
        articles.append(
            f"- Título: {item.get('title')}\n"
            f"  Fonte/URL: {item.get('url')}\n"
            f"  Resumo: {item.get('content')}\n"
        )

    return "\n".join(articles) if articles else "Nenhuma notícia recente encontrada."
