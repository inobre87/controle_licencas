# AGENTES.md

Guia para agentes de codigo que trabalham neste repositorio.

## Objetivo do projeto

Aplicacao Django para controle de licencas de software, com:
- cadastros (fornecedor, compra/NF, produto, departamento);
- gestao de licencas (livre/em uso);
- dashboard e relatorios;
- exportacao para Excel e PDF.

## Estrutura principal

- `controle_licencas/`: configuracao Django (settings, urls, wsgi/asgi).
- `licencas/`: app principal (models, views, forms, admin, urls, migrations).
- `templates/`: templates HTML.
- `manage.py`: entrypoint de comandos Django.

## Setup rapido (ambiente local)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Comandos uteis para validar alteracoes

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Se houver mudanca em `models.py`, gere migracoes reais:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Regras para contribuicao de agentes

1. Mantenha mudancas pequenas e focadas.
2. Nao commite `.env`, banco local, midias ou segredos.
3. Ao alterar modelos Django:
   - atualizar migracoes;
   - revisar impactos em admin, forms, views e relatorios.
4. Preserve compatibilidade com os filtros e exportacoes existentes.
5. Evite renomear campos/modelos sem plano de migracao claro.
6. Sempre rode validacoes minimas antes de concluir a tarefa.

## Checklist antes de finalizar

- [ ] Codigo alterado esta consistente com o dominio de licencas.
- [ ] Migracoes estao criadas (quando necessario).
- [ ] Comandos de validacao executados sem erro.
- [ ] Mudancas documentadas no PR de forma objetiva.
