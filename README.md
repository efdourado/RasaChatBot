# Chatbot

Capaz de realizar agendamentos, responder perguntas gerais sobre saúde e muito mais, graças à sua integração com um BD em tempo real e a API do Gemini.

---

## Features

  * **Integração Real com Banco de Dados (Prisma & Postgres):**

      * As especialidades, médicos e horários são consultados diretamente do banco de dados, garantindo informações sempre atualizadas;
      * Os agendamentos são **salvos em tempo real** no banco de dados ao final do fluxo.

      * O bot verifica a agenda do médico no banco de dados e mostra **apenas os horários realmente livres** para a data escolhida pelo usuário.

  * **Gemini:**

      * O chatbot consegue entender frases complexas e já preencher os dados do agendamento, tornando a conversa mais fluida;
      * Se o usuário fizer uma pergunta que não seja sobre agendamentos (ex: "o que é bom para dor de cabeça?"), o bot utiliza a IA do Gemini para fornecer uma resposta útil, mantendo o usuário engajado.

  * **Fluxo de Agendamento:**

      * O usuário é guiado desde a escolha da especialidade até a seleção do médico e do horário;
      * Coleta de dados do paciente (nome e email) e criação de um registro no BD, se necessário;
      * Confirmação final com todos os detalhes (médico, especialidade, data, hora) e o **ID do agendamento** salvo no banco.

---

## Run

```.env
    GEMINI_API_KEY=
    DATABASE_API_URL=
    DATABASE_URL=
    ACTION_ENDPOINT_URL=
```

Terminais (recomendação: source .venv/bin/activate && deactivate (criação de um ambiente virtual)):

1. rasa train && npm run dev

2. npm run rasa:actions

3. npm run rasa:server

4. npx prisma studio (opcional)

5. Abrir o 'frontend/index.html` em seu navegador.

docker: docker build -t chatbot . && docker run -p 5005:8080 -e PORT=8080 --rm chatbot

---

## Demo

  * Info
![alt text](image-1.png)

  * Conversa (em 3 prints)
![alt text](image-2.png)
![alt text](image-3.png)
![alt text](image-4.png)

  * Resultado no BD (Criação do Paciente +Consulta)
![alt text](image-5.png)
![alt text](image-6.png)

  * Banco e bot com horários atualizados (não mostra novamente o horário das 9h na segunda)
![alt text](image-7.png)

---

## Roadmap

  * Cancelar ou alterar seus agendamentos.
  * Permitir que o usuário veja suas consultas passadas e futuras.