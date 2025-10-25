# 🛡️ FactShield: Sentinel — O Escudo Contra a Desinformação
<div>
  <img src="https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Django-5.2-green?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/Pytest-Testing-blueviolet?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest">
  <img src="https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Ready">
  <img src="https://img.shields.io/badge/Queue-Celery-darkgreen?style=for-the-badge&logo=celery&logoColor=white" alt="Celery">
  <img src="https://img.shields.io/badge/Cache%2FBroker-Redis-red?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/AI%20Analysis-Gemini%20API-informational?style=for-the-badge&logo=google&logoColor=white" alt="Gemini API">
  <img src="https://img.shields.io/badge/Security-VirusTotal-darkblue?style=for-the-badge&logo=virustotal&logoColor=white" alt="VirusTotal">
  <img src="https://img.shields.io/badge/Scraping-Firecrawl-orange?style=for-the-badge" alt="Firecrawl API">
</div>

## 💡 Visão Geral do Projeto

**FactShield: Sentinel** é uma API de *backend* desenvolvida para combater a desinformação e as ameaças online. O projeto implementa um sistema de defesa em multicamadas que combina segurança cibernética e análise semântica avançada (LLM) para fornecer um veredito de credibilidade e risco para qualquer URL.

**Status Atual:** **MVP Funcional** com arquitetura assíncrona pronta para *deploy*. O foco está agora na qualidade de código e automação (Testes/CI).

---

## 🚀 O Grande Diferencial: Arquitetura de Alto Desempenho

O principal desafio de *backend* foi orquestrar quatro APIs com latências variadas de forma eficiente.

### 1. Concorrência Otimizada (`ThreadPoolExecutor`)

* **Técnica:** Utilização do **`concurrent.futures.ThreadPoolExecutor`** para rodar todas as chamadas de APIs externas (VT, Fact-Check, LLM) em paralelo.
* **Resultado Quantitativo Comprovado:** A otimização eliminou o tempo ocioso, reduzindo a latência do processo interno de **$17.86s$**+ (sequencial) para apenas **$\mathbf{13.55s}$** (limitado pelo processo mais lento).
* **Conclusão:** O *backend* agora opera no tempo mínimo de execução possível.

### 2. Arquitetura Assíncrona para UX (Próxima Fase)

* **Objetivo:** Eliminar a latência de $\mathbf{13.55s}$ para o usuário final.
* **Tecnologias:** Uso de **Celery** (Task Queue) e **Redis** (Broker & Cache) para garantir que a `APIView` retorne em menos de $150ms$, enquanto o trabalho de $13.55s$ ocorre em segundo plano.

---

## 🔍 Módulos e Pipeline de Análise em Camadas

O sistema de verificação funciona em hierarquia de veredito:

| Camada | Serviço/Tecnologia | Propósito |
| :--- | :--- | :--- |
| **0. Extração de Dados** | **Firecrawl API** | Extração robusta do conteúdo (`content`) e metadados (`title`) da URL, resolvendo falhas comuns de *web scraping*. |
| **1. Segurança Cibernética** | **VirusTotal API** | Checagem de *blacklists* e malware na URL (executando em paralelo). |
| **2. Checagem Humana** | **Google Fact Check Tools API** | Primeira linha de defesa. Busca vereditos de agências de *fact-checking*. Se houver veredito, ele é **prioritário** na decisão final. |
| **3. Inteligência Artificial** | **Google GenAI SDK (Gemini)** | Última linha de defesa. Usa **Prompt Engineering** para análise semântica do texto, buscando sinais de risco contextual (ex: desinformação temporal) e fornecendo a recomendação final (`PROSSIGA COM CAUTELA`). |

---

## 🏗️ Arquitetura e Tecnologia

| Componente | Tecnologia | Uso no Projeto |
| :--- | :--- | :--- |
| **Assincronia Principal** | **Celery & Redis** | *Task Queue* para rodar o pipeline no *background* e **Cache** para respostas instantâneas (24h TTL). |
| **Concorrência** | **`ThreadPoolExecutor`** | Paralelismo de chamadas I/O-bound (chaves para a redução de $\mathbf{17.86s}$+ para $\mathbf{13.55s}$). |
| **Servidor Produtivo** | **Gunicorn** | Pronto para substituir o servidor de desenvolvimento e garantir a segurança em *deploy*. |
| **Segurança/API Keys** | **`python-decouple`** | Gerenciamento seguro de todas as chaves de API. |
| **Containerização** | **Docker / Docker Compose** | Isolamento completo do ambiente (Web, Redis, Worker Celery). |

## ✅ Próximos Passos (Roadmap de Qualidade)

A fase de desenvolvimento de funcionalidade está concluída. O foco agora é na qualidade de código e automação:

1.  **Testes Unitários e de Integração:** Criar testes robustos para todos os módulos de serviço (ex: `search_fact_check`) e simular o fluxo assíncrono (usando *mocks* para APIs externas).
2.  **CI/CD com GitHub Actions:** Configurar o *pipeline* de integração contínua para rodar *linting* e **todos os testes** automaticamente antes de qualquer *merge* para `main`.
3.  **APIView e Caching:** Implementar a `APIView` de status e finalizar a lógica de *caching* para encerrar a fase de *backend*.
4.  **WebSockets (Melhoria Futura):** Migrar o *polling* de status para WebSockets para notificações em tempo real.
