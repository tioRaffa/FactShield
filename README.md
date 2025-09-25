# 🛡️ FactShield: Sentinel — O Escudo Contra a Desinformação

![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento%20Inicial-orange)

## 💡 Visão Geral do Projeto

**FactShield: Sentinel** é uma API de backend projetada para combater a desinformação digital e as ameaças online através de uma análise em camadas de links e conteúdos textuais. Em um cenário digital onde a propagação de "fake news" e links maliciosos é constante, o FactShield visa fornecer um veredito de credibilidade e segurança, utilizando o poder de APIs especializadas e Inteligência Artificial.

O projeto está em suas **fases iniciais de desenvolvimento**, focado na modelagem do banco de dados, configuração do ambiente Docker e integração inicial com serviços externos para estabelecer uma base sólida para as funcionalidades futuras.

## 🤔 Por que FactShield?

A desinformação digital representa uma ameaça crescente à sociedade, erodindo a confiança e influenciando decisões importantes. Identificar e mitigar a propagação de conteúdos falsos ou enganosos é um desafio complexo. O FactShield nasce da necessidade de uma ferramenta automatizada e inteligente que possa auxiliar desenvolvedores e plataformas a protegerem seus usuários, oferecendo um mecanismo confiável para validar a autenticidade e a segurança das informações compartilhadas.

## 🏗️ Arquitetura e Tecnologia

Este projeto foi construído para ser moderno, escalável e de alto desempenho, utilizando as seguintes ferramentas:

| Componente | Tecnologia | Propósito |
| :--- | :--- | :--- |
| **Linguagem Principal** | **Python 3.x** | Base de todo o desenvolvimento backend. |
| **Framework API** | **Django REST Framework (DRF)** | Construção de endpoints robustos, seguros e com foco em performance. |
| **Containerização** | **Docker / Docker Compose** | Isolamento completo do ambiente de desenvolvimento, facilitando o setup em diferentes máquinas e o futuro deploy. |
| **Cache e Controle** | **Redis** | Utilizado como camada de caching para respostas rápidas e para implementar o controle de taxa de requisições (*Rate Limiting*), garantindo a estabilidade e disponibilidade da API. |
| **Utilitários** | `python-decouple`, `django-extensions` | Gerenciamento seguro de variáveis de ambiente e ferramentas que aumentam a produtividade no desenvolvimento (ex: `runserver_plus`). |

## 🔍 Módulos e Fluxo de Análise (O Core da API)

O coração do FactShield é o seu sistema de verificação em três camadas. Uma requisição de análise de URL passará sequencialmente pelo seguinte fluxo, garantindo uma validação completa:

### Camada 1: Segurança (Vírus e Malware)

| Serviço | Propósito | Status |
| :--- | :--- | :--- |
| **VirusTotal API** | É a primeira e crucial verificação de segurança. O link fornecido é submetido à API do VirusTotal para identificar rapidamente qualquer associação com malware, phishing, scam ou outros riscos conhecidos de segurança. | **Integração em Andamento.** |

### Camada 2: Credibilidade (Conteúdo e Contexto)

| Serviço | Propósito | Status |
| :--- | :--- | :--- |
| **API de Conteúdo (A Definir)** | Após a validação de segurança, esta camada extrai o conteúdo principal da página da URL. O texto e metadados são então enviados para um serviço de terceiros (ainda a ser selecionado) que fará uma análise inicial da credibilidade da fonte, data de publicação e outros fatores contextuais. | **Integração Planejada.** |

### Camada 3: Inteligência Artificial (Veredito Final e Recomendações)

| Serviço | Propósito | Status |
| :--- | :--- | :--- |
| **API de IA (A Definir)** | Caso as camadas anteriores não consigam fornecer um veredito claro ou completo, o conteúdo é encaminhado para um modelo de Inteligência Artificial (Large Language Model - LLM). A IA realiza uma análise semântica profunda do texto, buscando padrões de desinformação, e fornece uma decisão final sobre a veracidade do conteúdo, acompanhada de **recomendações** e um resumo para o usuário. | **Integração Planejada.** |

## 🛠️ Configuração e Execução Local (Docker)

Para colocar o projeto no ar em seu ambiente de desenvolvimento, você deve usar o `docker-compose` para iniciar todos os serviços necessários (web e redis).

### Pré-requisitos

* Docker e Docker Compose devidamente instalados em sua máquina.
* Chaves de API (para VirusTotal e futuros serviços) configuradas em um arquivo `.env` na raiz do projeto. (Um `.env.example` será fornecido).

### Comandos de Inicialização

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/tioRaffa/FactShield.git
    cd factshield
    ```

2.  **Crie o arquivo de variáveis de ambiente:**
    ```bash
    cp .env.example .env
    # Edite o arquivo .env com suas chaves de API e configurações
    ```

3.  **Inicie o ambiente (Build e Run):**
    O Docker fará o build da imagem do Python, iniciará o serviço do Redis e, através do script de inicialização (`commands.sh`), aguardará a prontidão do Redis para então executar as migrações do Django.

    ```bash
    docker-compose up --build
    ```

### Acesso à API

Após a inicialização bem-sucedida, o serviço principal da API estará acessível em: `http://localhost:8000`

## 🚀 Próximos Passos (Roadmap)

Os próximos marcos importantes no desenvolvimento do FactShield incluem:

* Implementar a lógica de *Rate Limiting* e caching avançado com Redis para todos os endpoints relevantes.
* Finalizar e refinar a integração com a API do VirusTotal.
* Pesquisar, selecionar e desenvolver a camada de abstração para integração com as APIs de Conteúdo e Inteligência Artificial.
* Criação de testes unitários e de integração para todas as funcionalidades implementadas.
