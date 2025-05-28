# Chatbot de Agendamento - Clínica Super Saudável

Bem-vindo ao Chatbot de Agendamento da Clínica Super Saudável! Este é um assistente virtual desenvolvido com Rasa para ajudar os usuários a marcar consultas, obter informações sobre especialidades médicas, exames e detalhes da clínica.

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

1.  **Pré-requisitos:**
    * Python 3.x
    * Rasa Open Source (`pip install rasa`)

2.  **Treinar o Modelo Rasa:**
    Se você fez alterações nos arquivos de dados (`data/`), configuração (`config.yml`) ou domínio (`domain.yml`), treine um novo modelo:
    ```bash
    rasa train
    ```

3.  **Iniciar o Servidor de Ações:**
    Em um terminal, navegue até a raiz do projeto e execute:
    ```bash
    rasa run actions
    ```

4.  **Iniciar o Servidor Rasa:**
    Em outro terminal, navegue até a raiz do projeto e execute:
    ```bash
    rasa run --enable-api --cors "*"
    ```

5.  **Interagir com o Chatbot:**
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

* **Dados Mocados:** As especialidades, exames e, crucialmente, os horários disponíveis são fixos no código (`actions/actions.py`) e não vêm de um banco de dados real.
* **Agendamento Simulado:** O processo de agendamento não salva a consulta em um sistema persistente; ele apenas simula o sucesso e gera um ID aleatório.
* **Compreensão de Linguagem Natural (NLU):** A capacidade de entender variações de frases é limitada aos exemplos fornecidos no arquivo `data/nlu.yml`. Frases muito diferentes podem não ser compreendidas corretamente.
* **Informações da Clínica:** As informações como endereço e telefone são placeholders.
* **Tratamento de Datas:** A lógica de disponibilidade de horários no `actions.py` é simplificada e focada em "hoje" e "amanhã" para os dados mocados. Outras especificações de data podem não encontrar correspondência nos horários mocados.
* **Sem Gerenciamento de Usuários:** Não há autenticação ou personalização baseada no usuário.
* **Sem Cancelamento/Remarcação:** O bot atualmente não suporta cancelar ou remarcar consultas.

## 💡 Possíveis Melhorias Futuras

* **Integração com Banco de Dados Real:** Conectar o chatbot a um sistema de agendamento real para verificar disponibilidade e salvar consultas.
* **Expandir NLU:** Adicionar mais exemplos de treinamento para melhorar a compreensão de diferentes formas de perguntar a mesma coisa.
* **Melhorar Tratamento de Datas e Horas:** Implementar uma lógica mais robusta para lidar com diversas formas de especificar datas e períodos.
* **Funcionalidade de Cancelamento/Remarcação:** Permitir que os usuários gerenciem seus agendamentos.
* **Autenticação de Usuário:** Implementar um sistema de login para carregar dados do paciente e histórico.
* **Informações Dinâmicas da Clínica:** Puxar informações da clínica (endereço, contato, convênios) de uma fonte atualizável.
* **Fluxos de Conversa Mais Robustos:** Melhorar o tratamento de erros e caminhos alternativos na conversa.
* **Internacionalização:** Suporte a múltiplos idiomas.

---

Divirta-se interagindo com o Chatbot da Clínica Super Saudável!