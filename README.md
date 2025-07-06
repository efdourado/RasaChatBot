# Chatbot de Agendamento - Clínica Super Saudável

Bem-vindo ao Chatbot de Agendamento da Clínica Super Saudável\! Este é um assistente virtual inteligente desenvolvido com Rasa, capaz de realizar agendamentos de ponta-a-ponta, responder perguntas gerais sobre saúde e muito mais, graças à sua integração com um banco de dados em tempo real e a API do Google Gemini.

## ✨ Funcionalidades Principais

O chatbot agora está mais robusto e inteligente. As principais funcionalidades incluem:

  * **Integração Real com Banco de Dados (Prisma & SQLite):**

      * As especialidades, médicos e horários são consultados diretamente do banco de dados, garantindo informações sempre atualizadas.
      * Os agendamentos são **salvos em tempo real** no banco de dados ao final do fluxo.

  * **Verificação de Disponibilidade em Tempo Real:**

      * O bot verifica a agenda do médico no banco de dados e mostra **apenas os horários realmente livres** para a data escolhida pelo usuário.

  * **Inteligência Artificial com Google Gemini:**

      * **Extração Inteligente de Informações:** O chatbot consegue entender frases complexas como *"quero agendar com um cardiologista para amanhã à tarde"* e já preencher os dados do agendamento, tornando a conversa mais fluida.
      * **Respostas a Perguntas Gerais:** Se o usuário fizer uma pergunta que não seja sobre agendamentos (ex: "o que é bom para dor de cabeça?"), o bot utiliza a IA do Gemini para fornecer uma resposta útil, mantendo o usuário engajado.

  * **Fluxo de Agendamento de Ponta-a-Ponta:**

      * O usuário é guiado desde a escolha da especialidade até a seleção do médico e do horário.
      * Coleta de dados do paciente (nome e e-mail) e criação de um registro no banco de dados, se necessário.
      * Confirmação final com todos os detalhes (médico, especialidade, data, hora) e o **ID do agendamento real** salvo no banco.

## 🚀 Como Executar o Projeto

### Configuração Inicial

1.  **Pré-requisitos:**

      * Python 3.x
      * Node.js e npm
      * Rasa Open Source (`pip install rasa`)

2.  **Variáveis de Ambiente:**
    Crie um arquivo `.env` na raiz do projeto. Ele é **essencial** para a integração com o banco de dados e a IA do Gemini.

    ```bash
    # Conteúdo do arquivo .env

    # Chave de API para o Google Gemini
    GEMINI_API_KEY="SUA_API_KEY_AQUI"

    # Caminho do banco de dados (padrão)
    DATABASE_URL="file:./dev.db"
    ```

3.  **Configurar o Banco de Dados e Dependências:**
    Este comando irá instalar as dependências Node.js e popular o banco de dados com dados de exemplo.

    ```bash
    npm install
    npm run seed
    ```

### Execução do Chatbot

1.  **Treinar o Modelo Rasa:**
    (Se você fez alterações nos arquivos `.yml`)

    ```bash
    rasa train
    ```

2.  **Iniciar o Servidor de Ações:**
    (Em um terminal)

    ```bash
    rasa run actions
    ```

3.  **Iniciar o Servidor Rasa:**
    (Em outro terminal)

    ```bash
    rasa run --enable-api --cors "*"
    ```

4.  **Interagir com o Chatbot:**

      * Abra o arquivo `frontend/index.html` em seu navegador web.
      * Ou interaja pela linha de comando: `rasa shell`.

## 🗣️ Exemplos de Conversa

Você pode começar com "Olá". O bot agora entende uma variedade de comandos:

  * **Simples:** "Quero marcar uma consulta"
  * **Direto:** "Gostaria de agendar com Cardiologia"
  * **Inteligente (com Gemini):** "preciso de um clínico geral para hoje à tarde"
  * **Geral (com Gemini):** "o que causa enxaqueca?"
  * "Quais especialidades vocês atendem?"
  * "Qual o endereço de vocês?"

## 🗄️ Detalhes do Banco de Dados

O projeto utiliza Prisma ORM com SQLite para uma gestão de dados robusta e de fácil manutenção. Para mais detalhes técnicos, como schema e operações, consulte o arquivo **[DATABASE\_README.md]**.

  * **Ver a base de dados em uma interface gráfica:** `npm run prisma:studio`
  * **Resetar e popular a base com dados de exemplo:** `npm run seed`

## 💡 Próximos Passos e Melhorias

  * **Cancelamento e Remarcação:** Implementar um fluxo para que os usuários possam cancelar ou alterar seus agendamentos.
  * **Autenticação de Usuário:** Criar um sistema de login para que pacientes recorrentes tenham uma experiência personalizada.
  * **Histórico de Consultas:** Permitir que o usuário veja suas consultas passadas e futuras.

-----

Espero que este novo `README.md` ajude a refletir o excelente trabalho que vocês fizeram no projeto\! Se precisar de mais alguma coisa, é só pedir.