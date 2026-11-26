# MercadoSimples — Plataforma de E-Commerce

Integrantes:

- Flavio Gabriel Soares Melo
- Manuel Junio Ferraz Cardoso

## Sobre o sistema

O **MercadoSimples** é uma aplicação web de comércio eletrônico (marketplace) desenvolvida em Python na qual usuários interagem por meio de dois perfis de conta:

- **Anunciante**: pode cadastrar produtos para venda (com título, descrição, categoria, preço, estoque e imagem por upload ou URL), gerenciar seus itens anunciados (alterar preço rapidamente, editar dados completos ou remover anúncios) e consultar seu **saldo a receber** juntamente com o extrato detalhado das vendas realizadas.
- **Cliente**: pode explorar o catálogo público, pesquisar itens por palavra-chave, filtrar por categoria, ordenar por preço, adicionar produtos de diferentes vendedores ao **carrinho de compras**, ajustar quantidades e aprovar o pagamento simulado de todos os itens de uma única vez, além de consultar o histórico de pedidos pagos.

O sistema de pagamento é intencionalmente simplificado para fins acadêmicos: ao confirmar a compra no carrinho, o pagamento é aprovado instantaneamente sem envolver dinheiro real, deduzindo o estoque dos itens comprados e creditando automaticamente o valor correspondente no saldo de cada anunciante.

## Tecnologias

- **Python 3.12**: linguagem principal utilizada em toda a lógica de domínio, persistência, servidor web e testes.
- **Flask + Jinja2 + CSS3**: framework web leve responsável pelas rotas HTTP, sessões de usuário, upload de imagens e renderização das páginas HTML responsivas.
- **SQLite (`sqlite3`)**: banco de dados relacional embarcado utilizado para persistência transacional de usuários, produtos, pedidos e saldo, com suporte a banco em memória nos testes automatizados.
- **Pytest**: framework utilizado para organizar e executar os testes de unidade e de integração.
- **Playwright (Python)**: framework utilizado nos testes *end-to-end* (E2E) com navegador Chromium real em modo *headless*.
- **Coverage.py**: ferramenta utilizada para aferir a cobertura de código e linhas/ramificações (configurada para exigir cobertura ≥ 80% e gerar `coverage.xml` compatível com o Codecov).
- **Gunicorn**: servidor WSGI pronto para publicação em plataformas de nuvem gratuitas (como Render ou Fly.io).

## Uso de IA

Foram utilizadas ferramentas de IA para desenvolvimento do sistema e criação dos testes, sempre com supervisão humana. Cada commit foi feito manualmente após revisão de todas as alterações sugeridas.

## Execução dos testes

### 1. Preparar o ambiente virtual

Na raiz do projeto, crie o ambiente virtual, ative-o e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Executar os testes de unidade

```bash
pytest testes/unidade -v
```

### 3. Executar os testes end-to-end (E2E)

```bash
pytest testes/e2e -v
```

### 4. Executar toda a suíte mensurando cobertura (≥ 80%)

```bash
coverage run -m pytest -v
coverage report --fail-under=80
coverage html  # Opcional: gera relatório navegável em htmlcov/index.html
```

## Execução local da aplicação

Com o ambiente virtual ativo, inicie o servidor local:

```bash
python app.py
```

Acesse no navegador: `http://localhost:5000`

## Publicação em produção

A aplicação lê automaticamente variáveis de ambiente (`SECRET_KEY`, `PORT`, `CAMINHO_BANCO`, `PASTA_UPLOADS`) e acompanha os arquivos `Procfile` e `render.yaml` prontos para deploy gratuito no **Render** (ou serviços equivalentes como Railway e Fly.io) utilizando `gunicorn app:app` com rota de verificação de integridade em `/saude`.
