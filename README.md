# Chatbot de Agendamento

Bem-vindo ao assistente virtual inteligente desenvolvido com Rasa, capaz de realizar agendamentos, responder perguntas gerais sobre saúde e muito mais, graças à sua integração com um banco de dados em tempo real e a API do Gemini.

## ✨ Features

O chatbot agora está mais robusto e inteligente. As principais funcionalidades incluem:

  * **Integração Real com Banco de Dados (Prisma & SQLite):**

      * As especialidades, médicos e horários são consultados diretamente do banco de dados, garantindo informações sempre atualizadas.
      * Os agendamentos são **salvos em tempo real** no banco de dados ao final do fluxo.

  * **Verificação de Disponibilidade em Tempo Real:**

      * O bot verifica a agenda do médico no banco de dados e mostra **apenas os horários realmente livres** para a data escolhida pelo usuário.

  * **IA com Google Gemini:**

      * **Extração Inteligente de Informações:** O chatbot consegue entender frases complexas como *"quero agendar com um cardiologista para amanhã à tarde"* e já preencher os dados do agendamento, tornando a conversa mais fluida.
      * **Respostas a Perguntas Gerais:** Se o usuário fizer uma pergunta que não seja sobre agendamentos (ex: "o que é bom para dor de cabeça?"), o bot utiliza a IA do Gemini para fornecer uma resposta útil, mantendo o usuário engajado.

  * **Fluxo de Agendamento de Ponta-a-Ponta:**

      * O usuário é guiado desde a escolha da especialidade até a seleção do médico e do horário.
      * Coleta de dados do paciente (nome e e-mail) e criação de um registro no banco de dados, se necessário.
      * Confirmação final com todos os detalhes (médico, especialidade, data, hora) e o **ID do agendamento real** salvo no banco.

## 🚀 Run

.env:

```bash
    GEMINI_API_KEY=
    DATABASE_API_URL=
    DATABASE_URL=
    ACTION_ENDPOINT_URL=
```


```bash
    rasa train

    npm run dev
```

```bash
    npm run rasa:actions
```

```bash
    npm run rasa:server
```

```bash
    npx prisma studio
```

Abra `frontend/index.html` em seu navegador ou interaja pela linha de comando: `rasa shell`.

## 🗣️ Exemplos de conversa

  * "Quero marcar uma consulta"
  * "Gostaria de agendar com Cardiologia"
  * "preciso de um clínico geral para hoje à tarde"
  * "o que causa enxaqueca?"
  * "Quais especialidades vocês atendem?"
  * "Qual o endereço de vocês?"

## 💡 Roadmap

  * **Cancelamento e Remarcação:** Implementar um fluxo para que os usuários possam cancelar ou alterar seus agendamentos.
  * **Autenticação de Usuário:** Criar um sistema de login para que pacientes recorrentes tenham uma experiência personalizada.
  * **Histórico de Consultas:** Permitir que o usuário veja suas consultas passadas e futuras.