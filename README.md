# Cabeleleila Leila Salão de Beleiza - Sistema de Agendamentos

## Sobre o Projeto
Este sistema foi desenvolvido como solução para o salão "Cabeleleila Leila", permitindo que clientes realizem agendamentos online de serviços de beleza, visualizem seus históricos e façam alterações. Além disso, o sistema conta com um painel gerencial exclusivo para a administração do salão.

## Tecnologias Utilizadas
* **Backend:** Python e Django
* **Banco de Dados:** SQLite3 (Padrão do Django, ideal para facilitar a execução local)
* **Frontend:** HTML5, CSS3, e Template Engine do Django
* **Testes:** `unittest` nativo do Django
* **Padronização de Código:** Flake8 (PEP 8)

## Como Rodar o Projeto na Sua Máquina

Siga o passo a passo abaixo para executar o projeto localmente:

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/JeannAlves12/salao_leila
   cd salao_leila
   ```
   
2. **Crie e ative o ambiente virtual:**
   * No Windows:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
   * No Linux/Mac:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   
3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```
   
4. **Aplique as migrações no banco de dados:**
   ```bash
   python manage.py migrate
   ```
   
5. **Criar um usuário Administrador/Dono(Neste caso a Leila)**
   * passo importante para conseguir acessar a visão de gerncia do sistema.
   ```bash
   python manage.py createsuperuser
   ```
   ****Siga os passos na tela para definir usuário, email e senha.****

6. Inicie o servidor local:
   ```bash
   python manage.py runserver
   ```
   ****O sistema estará disponível no seu navegador no endereço: (http://127.0.0.1:8000/)****

## Observações e Funcionalidades Desenvolvidas

O sistema contempla todos os requisitos fundamentais e diferenciais solicitados: 

* **Gestão de Agendamentos:** Clientes podem agendar múltiplos serviços ao mesmo tempo.
* **Regra de Alteração (2 Dias):** Implementada trava de segurança. O cliente só consegue cancelar ou editar o agendamento via sistema com mais de 48h de antecedência. Menos do que isso, o sistema bloqueia e orienta a ligar para o salão.
* **Sugestão Inteligente de Data:** Caso o cliente tente agendar um novo serviço, o sistema verifica se ele já possui outro agendamento na mesma semana e sugere concentrar os serviços no mesmo dia.
* **Painel Gerencial:** A conta com privilégios de "Staff" (Dona) tem acesso a um dashboard exclusivo. Por lá, ela consegue burlar a regra dos 2 dias, alterar status dos serviços, confirmar agendamentos e ver métricas.
* **Arquitetura Limpa:** As views foram separadas modularmente por contexto (Cliente, Gerência, Autenticação, Serviços) para facilitar a manutenção.
* **Testes Unitários:** O projeto conta com testes unitários cobrindo as regras de negócio cruciais de validação de data e sugestão de agendamento (Para testar, rode python manage.py test).

## Notas de Desenvolvimento e Decisões Arquiteturais

Para garantir a manutenibilidade, a transparência e a escalabilidade do código, tomei as seguintes decisões técnicas durante o desenvolvimento:

* **Arquitetura MVT (Django):** O projeto foi estruturado seguindo o padrão MVT (Model-View-Template) do Django, que é a variação do framework para o clássico MVC. Optei por focar nessa arquitetura e nas ferramentas nativas do Django por ser o ecossistema onde me sinto mais confiante em desenvolver e entregar uma solução robusta dentro do prazo.
* **Foco no Backend e Uso de Ferramentas:** Como eu tenho um pouco mais de domínio na lógica do backend, utilizei ferramentas como apoio para a estruturação e estilização das páginas em HTML (área onde tenho menos prática) e também para auxiliar na resolução de erros pontuais durante o código. 
* **Isolamento de Regras de Negócio:** As lógicas mais complexas (como a trava de 2 dias e a sugestão de agendamentos na mesma semana) foram extraídas para um arquivo isolado (`services.py`). Isso evita que as *Views* e os *Models* fiquem sobrecarregados (Fat Models / Fat Views) e facilita a aplicação de testes unitários.
* **Modularização das Views:** O projeto não utiliza um único arquivo `views.py` gigante. As rotas foram separadas em (`client_views.py`, `owner_views.py`, `auth_views.py`, etc.), tornando a navegação pelo projeto muito mais simples e fácil de entender.
* **Uso de FBVs vs CBVs:** Optei por construir o sistema utilizando *Function-Based Views (FBVs)* para manter o fluxo de dados o mais explícito e legível possível. No entanto, por curiosidade pesquisei como ficaria a arquitetura com *Class-Based Views (CBVs)* no futuro. Por isso a existência da pasta (`cbv`) dentro de (`appointments`). 


## Pasta ('evidencias')

Contém imagens pedidas para avaliação.