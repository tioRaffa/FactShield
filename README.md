# 🛡️ FactShield: Sentinel — O Escudo Contra a Desinformação

## 💡 Visão Geral do Projeto

**FactShield: Sentinel** é uma API de *backend* projetada para combater a desinformação digital e as ameaças online através de uma **análise em pipeline otimizada**. O projeto implementa um sistema de defesa em multicamadas que combina segurança cibernética e análise semântica avançada para fornecer um veredito de credibilidade e risco de segurança para qualquer URL.

O projeto está na fase de **MVP Funcional**, com todas as camadas de análise integradas e o desafio de *backend* de **latência zero** em andamento (transição para Celery/Redis).

-----

## 🚀 O Grande Diferencial: Arquitetura de Alto Desempenho

O principal desafio de *backend* era orquestrar quatro APIs lentas e variadas de forma eficiente.

### 1\. Concorrência Síncrona (Otimização Comprovada)

  * **Técnica:** Utilização de **`concurrent.futures.ThreadPoolExecutor`** para rodar chamadas de APIs externas (VirusTotal, Google Fact Check, LLM) em paralelo.
  * **Resultado Quantitativo:** A aplicação desta técnica reduziu drasticamente o tempo de processamento *worst-case* da API:
    $$\text{Latência Média Reduzida de} \mathbf{17.86s} \text{ para } \mathbf{13.55s} \text{ (Tempo do Processo Mais Lento)}$$
  * **Conclusão:** O sistema já executa toda a análise no tempo mínimo possível, provando a eficiência do design.

### 2\. Próximo Passo: Latência Zero para o Usuário (Assincronia)

  * **Fase Atual:** Preparação para migrar o processo de $\mathbf{13.55s}$ para o *background*.
  * **Tecnologias:** Implementação do **Celery** (como *Task Queue*) e **Redis** (como *Broker* e *Cache*) para garantir que a `APIView` retorne em menos de $150ms$, enquanto a análise ocorre em segundo plano.

-----

## 🔍 Módulos e Pipeline de Análise em Camadas

O sistema de verificação em quatro camadas está totalmente integrado, funcionando em hierarquia de veredito (priorizando a fonte humana).

| Camada | Serviço/Tecnologia | Propósito e Veredito |
| :--- | :--- | :--- |
| **0. Extração de Dados** | **Firecrawl API** | Extração robusta do `title` e do `content` principal da URL (resolvendo o problema de *scraping* em sites complexos). |
| **1. Segurança Cibernética** | **VirusTotal API** | Checagem de *blacklists* e malware na URL. Rodando **em paralelo** com as análises de conteúdo. |
| **2. Checagem Humana** | **Google Fact Check Tools API** | Primeira linha de defesa. Busca vereditos de agências humanas (ex: Estadão Verifica). O veredito é **prioritário** no relatório final. |
| **3. Inteligência Artificial** | **Google GenAI SDK (Gemini)** | Última linha de defesa. Usa *Prompt Engineering* para analisar o conteúdo completo, gerar um resumo, avaliar o **risco contextual** e fornecer uma recomendação (ex: **"PROSSIGA COM CAUTELA"**). |

-----

## 🏗️ Arquitetura e Tecnologia

| Componente | Tecnologia | Uso no Projeto |
| :--- | :--- | :--- |
| **Orquestração** | **Celery & Redis** | Migrando o pipeline completo para execução assíncrona. **Redis** também será usado para *caching* de resultados (latência zero). |
| **Concorrência** | **`ThreadPoolExecutor`** | Paralelismo de chamadas I/O-bound (chaves para a redução de $\mathbf{17.86s}$ para $\mathbf{13.55s}$). |
| **Linguagem/Framework** | **Python 3.x, Django REST** | Base robusta para o desenvolvimento *backend* da API. |
| **Segurança/API Keys** | **`python-decouple`** | Gerenciamento seguro de todas as chaves de API externas (VT, Firecrawl, Gemini, Google Fact Check). |
| **Containerização** | **Docker / Docker Compose** | Isolamento do ambiente de desenvolvimento (API, Redis e Worker Celery). |

## 🚀 Próximos Passos (Roadmap)

1.  **Implementar Celery Task:** Finalizar a transformação da função `run_full_analysis_synchronous` em um `@shared_task`.
2.  **APIView Assíncrona:** Criar a View que gerencia o *caching* com Redis e dispara a Task, retornando o `HTTP 202 Accepted` com o Job ID.
3.  **Configurar WebSockets (Melhoria Futura):** Implementar *WebSockets* (ex: Django Channels) para notificar o *frontend* instantaneamente quando a análise de $\mathbf{13.55s}$ for concluída.
