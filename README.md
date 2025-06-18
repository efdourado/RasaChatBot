# Chatbot de Agendamento - Clínica Super Saudável

Bem-vindo ao Chatbot de Agendamento da Clínica Super Saudável! Este é um assistente virtual desenvolvido com Rasa para ajudar os usuários a marcar consultas, obter informações sobre especialidades médicas, exames e detalhes da clínica.

## 🗄️ Novidade: Sistema de Banco de Dados

Este projeto agora inclui um **sistema de banco de dados completo** usando Prisma ORM com SQLite. O banco de dados está pronto para integração com o chatbot e inclui:

- ✅ **Modelos de dados** para Pacientes, Médicos, Especialidades e Agendamentos
- ✅ **Base de dados funcional** com dados de exemplo
- ✅ **API TypeScript** para operações CRUD
- ✅ **Scripts de gerenciamento** para seed, migração e reset
- ✅ **Interface gráfica** com Prisma Studio

📖 **Para mais detalhes sobre o banco de dados, consulte: [DATABASE_README.md](DATABASE_README.md)**

### Scripts do Banco de Dados:
```bash
npm run seed              # Popula o banco com dados de exemplo
npm run prisma:studio     # Abre interface gráfica do banco
ts-node src/example.ts    # Executa exemplos de consultas
```

## ✨ Funcionalidades Principais

O chatbot é capaz de:

* **Saudações e Despedidas:** Iniciar e encerrar conversas de forma amigável.
* **Agendamento de Consultas:**
    * Perguntar e entender a **especialidade médica** desejada.
    * Coletar o **nome do paciente**.
    * Perguntar sobre a **data e hora preferida** para a consulta.
    * Verificar a **disponibilidade de horários** com base nas informações fornecidas (usando dados mocados).
    * Apresentar os **horários disponíveis** e permitir que o usuário escolha um.
    * **Confirmar os detalhes** do agendamento antes de finalizar.
    * Simular a **realização do agendamento**, fornecendo um ID fictício.
* **Informações sobre Especialidades:** Listar as especialidades médicas atendidas pela clínica.
* **Informações sobre Exames:** Listar os exames disponíveis para uma determinada especialidade.
* **Informações da Clínica:** Fornecer informações básicas sobre a clínica (atualmente com dados placeholder).
* **Interação Básica:** Responder a agradecimentos e identificar-se como um bot.
* **Ajuda:** Oferecer ajuda sobre o que ele pode fazer.

## 🚀 Como Executar o Projeto

### Configuração Inicial (Primeira vez):

1.  **Pré-requisitos:**
    * Python 3.x
    * Node.js e npm
    * Rasa Open Source (`pip install rasa`)

2.  **Configurar o Banco de Dados:**
    ```bash
    npm install
    npm run seed
    ```

### Execução do Chatbot:

1.  **Treinar o Modelo Rasa:**
    Se você fez alterações nos arquivos de dados (`data/`), configuração (`config.yml`) ou domínio (`domain.yml`), treine um novo modelo:
    ```bash
    rasa train
    ```

2.  **Iniciar o Servidor de Ações:**
    Em um terminal, navegue até a raiz do projeto e execute:
    ```bash
    rasa run actions
    ```

3.  **Iniciar o Servidor Rasa:**
    Em outro terminal, navegue até a raiz do projeto e execute:
    ```bash
    rasa run --enable-api --cors "*"
    ```

4.  **Interagir com o Chatbot:**
    * Abra o arquivo `frontend/index.html` em seu navegador web.
    * Ou, para interagir via linha de comando (certifique-se de que o servidor de ações está rodando):
        ```bash
        rasa shell
        ```

## 🗣️ Como Conversar com o Bot (Exemplos)

Você pode iniciar a conversa com um simples "Olá". Aqui estão alguns exemplos do que você pode dizer:

* "Quero marcar uma consulta"
* "Gostaria de agendar com Cardiologia"
* "Meu nome é Teste Feliz"
* "Para amanhã de manhã"
* "Quais especialidades vocês atendem?"
* "Quais exames tem para cardiologia?"
* "Qual o endereço de vocês?"
* "Obrigado"
* "Tchau"

## ⚠️ Limitações Atuais

* **Integração Pendente:** O banco de dados está configurado mas ainda não está integrado com as ações do Rasa (próximo passo!)
* **Dados Mocados no Bot:** As especialidades, exames e horários ainda vêm do código (`actions/actions.py`) até a integração ser completada
* **Agendamento Simulado:** O processo de agendamento não salva ainda no banco de dados real
* **Compreensão de Linguagem Natural (NLU):** A capacidade de entender variações de frases é limitada aos exemplos fornecidos no arquivo `data/nlu.yml`
* **Tratamento de Datas:** A lógica de disponibilidade de horários é simplificada
* **Sem Gerenciamento de Usuários:** Não há autenticação ou personalização baseada no usuário
* **Sem Cancelamento/Remarcação:** O bot atualmente não suporta cancelar ou remarcar consultas

## 💡 Próximos Passos

* **🔗 Integrar Banco com Rasa:** Conectar as ações do Rasa com o banco de dados Prisma
* **📊 Dados Dinâmicos:** Puxar especialidades e médicos do banco de dados em tempo real
* **💾 Salvar Agendamentos:** Persistir consultas no banco de dados
* **🔍 Busca de Disponibilidade:** Implementar verificação real de horários disponíveis
* **👤 Gestão de Pacientes:** Criar e gerenciar perfis de pacientes

## 💡 Possíveis Melhorias Futuras

* **Expandir NLU:** Adicionar mais exemplos de treinamento para melhorar a compreensão
* **Melhorar Tratamento de Datas e Horas:** Implementar uma lógica mais robusta para datas
* **Funcionalidade de Cancelamento/Remarcação:** Permitir que os usuários gerenciem seus agendamentos
* **Autenticação de Usuário:** Implementar um sistema de login
* **Informações Dinâmicas da Clínica:** Puxar informações da clínica de uma fonte atualizável
* **Fluxos de Conversa Mais Robustos:** Melhorar o tratamento de erros
* **Internacionalização:** Suporte a múltiplos idiomas

---

Divirta-se interagindo com o Chatbot da Clínica Super Saudável!




---

.env:

- GEMINI_API_KEY=SUA_API_KEY_AQUI
- DATABASE_URL=file:./dev.db

---

.gitignore:

- .venv/
- .rasa/

- node_modules/

- .env

- models/*.tar.gz
- dist/
- prisma/dev.db