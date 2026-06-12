# Agência Alvarenga — A/R

Loja streetwear com backend Flask + SQLite.

## Estrutura

```
agencia-alvarenga/
├── app.py                  # Backend Flask unificado
├── requirements.txt        # Dependências Python
├── templates/              # Templates Jinja2
│   ├── index.html
│   ├── sobre.html
│   ├── projeto.html
│   ├── loja.html
│   ├── cadastro.html
│   └── admin.html
├── static/
│   ├── css/                # Estilos globais (opcional)
│   ├── js/
│   │   └── salvar_email.js # Utilitário de captura de e-mail
│   └── img/                # Imagens da loja
└── instance/               # Banco SQLite (criado automaticamente, não versionar)
    └── banco.db
```

## Como rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Iniciar o servidor
python app.py
```

Acesse: http://127.0.0.1:5000

## Rotas

| Método | Rota                  | Descrição                     |
|--------|-----------------------|-------------------------------|
| GET    | `/`                   | Página inicial                |
| GET    | `/sobre`              | Sobre a agência               |
| GET    | `/projeto`            | Projetos                      |
| GET    | `/loja`               | Loja                          |
| GET    | `/cadastro`           | Formulário de cadastro        |
| POST   | `/cadastrar`          | Processa cadastro             |
| POST   | `/comprar`            | Processa compra               |
| POST   | `/login-cliente`      | Login do cliente (JSON)       |
| GET    | `/logout-cliente`     | Logout do cliente             |
| POST   | `/registrar-email`    | Captura e-mail (JSON)         |
| GET    | `/admin`              | Painel admin                  |
| POST   | `/admin/login`        | Login admin (JSON)            |
| POST   | `/admin/logout`       | Logout admin (JSON)           |
| GET    | `/api/admin/clientes` | Lista clientes (protegido)    |
| GET    | `/api/admin/metrics`  | Métricas do admin (protegido) |

## Admin padrão

- **Usuário:** `admin`
- **Senha:** `admin123`

Para alterar, defina as variáveis de ambiente `ADMIN_INITIAL_USERNAME` e `ADMIN_INITIAL_PASSWORD` antes do primeiro `python app.py`.

## Variáveis de ambiente

| Variável               | Padrão       | Descrição                  |
|------------------------|--------------|----------------------------|
| `FLASK_SECRET_KEY`     | gerada       | Chave de sessão Flask      |
| `ADMIN_INITIAL_USERNAME` | `admin`    | Usuário admin inicial      |
| `ADMIN_INITIAL_PASSWORD` | `admin123` | Senha admin inicial        |
