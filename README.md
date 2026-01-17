# Controle de Licenças (Django)

Sistema web para cadastrar licenças (Windows/Office/Server/Corel etc.), vincular obrigatoriamente cada licença a uma Nota/Compra com PDF, e gerar relatórios em Excel e PDF + dashboard.

## Requisitos
- macOS com Python 3.10+ (recomendado 3.11)
- VS Code

## 1) Colocar o projeto na Mesa (Desktop)
- Descompacte o ZIP na sua **Mesa**.
- A pasta do projeto se chama: `controle_licencas`

## 2) Abrir no VS Code
- Abra o VS Code
- File > Open… > selecione a pasta `controle_licencas`

## 3) Criar e ativar o ambiente virtual
No Terminal do VS Code (View > Terminal):

```bash
cd ~/Desktop/controle_licencas
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4) Criar o arquivo .env
```bash
cp .env.example .env
```

## 5) Migrar o banco e criar o usuário admin
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## 6) Rodar
```bash
python manage.py runserver
```

Acesse:
- Dashboard: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Relatórios: http://127.0.0.1:8000/relatorios/

## Fluxo de uso (recomendado)
1. Admin → cadastre **Fornecedor**
2. Admin → cadastre **Compra/NF** e anexe o **PDF** (obrigatório)
3. Admin → cadastre **Produto** (ex.: Microsoft • Windows • 11 Pro)
4. Admin → cadastre **Licença** vinculando na Compra/NF (que tem o PDF)
   - status LIVRE/EM_USO
   - se EM_USO, informe o usuário atual

## Exportação
- Excel: botão "Baixar Excel"
- PDF: botão "Baixar PDF"
