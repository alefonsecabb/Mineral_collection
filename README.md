# 🪨 Coleção de Minérios — Pedro Faria da Fonseca

Catálogo digital da coleção pessoal de minérios de **Pedro Faria da Fonseca**.
Cada mineral cadastrado traz foto, fórmula química, dureza na escala de Mohs, sistema cristalino, curiosidades e principais usos.

---

## Sobre o Projeto

Esta aplicação web permite gerenciar e visualizar a coleção de minérios do Pedro.
Por meio de uma interface elegante com tema escuro, é possível:

- Adicionar novos minérios com foto (upload ou busca automática na internet)
- Consultar detalhes completos de cada mineral
- Editar ou remover registros
- Identificar minérios automaticamente com inteligência artificial (Claude AI)

---

## Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| Backend | Python 3 + Flask |
| Banco de dados | MongoDB |
| Frontend | Jinja2 + JavaScript + CSS |
| IA | Anthropic Claude (Sonnet 4.6) |
| Imagens | Wikimedia Commons API |

---

## Banco de Dados — MongoDB

A aplicação usa **MongoDB** como banco de dados NoSQL para armazenar os minérios da coleção.

### Estrutura

- **Banco:** `minerais_db`
- **Coleção:** `minerais`

### Documento de exemplo

```json
{
  "_id": "ObjectId(...)",
  "name": "Ametista",
  "description": "Variedade de quartzo de coloração violeta...",
  "curiosity": "A cor roxa é causada por impurezas de ferro...",
  "main_use": "Joalheria e colecionismo",
  "chemical_formula": "SiO₂",
  "hardness": 7.0,
  "crystal_system": "Trigonal",
  "image_path": "static/uploads/ametista.jpg",
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Conexão

A URI de conexão é definida no arquivo `.env`:

```
MONGO_URI=mongodb://localhost:27017
```

O arquivo `db.py` gerencia toda a comunicação com o banco:

- `find_all()` — lista todos os minérios
- `find_by_id(id)` — busca um mineral pelo ID
- `insert_mineral(data)` — cadastra novo mineral
- `update_mineral(id, data)` — atualiza um registro
- `delete_mineral(id)` — remove um registro

---

## Como Acessar o Site

### Pré-requisitos

- [Python 3.8+](https://www.python.org/downloads/)
- [MongoDB Community Server](https://www.mongodb.com/try/download/community) rodando localmente
- (Opcional) Chave de API da Anthropic para identificação por IA

### Passo a Passo

**1. Clone o repositório**

```bash
git clone https://github.com/alefonsecabb/Mineral_collection.git
cd Mineral_collection
```

**2. Instale as dependências**

```bash
pip install -r requirements.txt
```

**3. Configure o arquivo `.env`**

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```
MONGO_URI=mongodb://localhost:27017
ANTHROPIC_API_KEY=sua_chave_aqui   # opcional
```

**4. (Opcional) Popule o banco com minérios de exemplo**

```bash
python seed_db.py
```

**5. Inicie o servidor**

```bash
python app.py
```

**6. Acesse no navegador**

```
http://localhost:5000
```

---

## Funcionalidades

- **Galeria** — visualize todos os minérios cadastrados em grade responsiva
- **Detalhes** — veja informações completas de cada mineral, incluindo escala de Mohs visual
- **Adicionar** — cadastre um novo minério com upload de foto ou busca automática no Wikimedia Commons
- **Editar** — atualize qualquer informação do mineral
- **Remover** — exclua um mineral da coleção
- **IA** — com a chave da Anthropic configurada, a aplicação identifica o mineral pela foto ou pelo nome automaticamente

---

## Estrutura do Projeto

```
Mineral_collection/
├── app.py               # Servidor Flask e rotas
├── db.py                # Conexão e operações no MongoDB
├── claude_service.py    # Integração com Claude AI
├── mineral_database.py  # Base de dados offline com 20+ minérios
├── seed_db.py           # Script para popular o banco
├── requirements.txt     # Dependências Python
├── .env                 # Variáveis de ambiente (não versionado)
├── static/
│   ├── css/style.css    # Estilo com tema escuro
│   ├── js/main.js       # Interações do frontend
│   └── uploads/         # Imagens dos minérios
└── templates/
    ├── base.html        # Template base
    ├── index.html       # Galeria
    ├── add.html         # Formulário de adição
    ├── detail.html      # Página de detalhes
    └── edit.html        # Formulário de edição
```

---

*Coleção de Pedro Faria da Fonseca*
