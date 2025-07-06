# 1. Usar a imagem oficial do Rasa como base.
# Ela já vem com Python, um ambiente virtual e um usuário não-root configurado.
FROM rasa/rasa:3.6.10-full

# 2. Copiar todos os arquivos do seu projeto para o diretório de trabalho no container.
# O diretório de trabalho padrão na imagem base é /app.
COPY . .

# 3. Instalar as dependências Python para suas actions.
# O usuário da imagem base já tem as permissões corretas para fazer isso.
RUN pip install -r actions/requirements.txt

# 4. Treinar o modelo Rasa.
# Este passo é necessário para o chatbot-rasa-server.
RUN rasa train

# 5. O comando para iniciar o serviço será definido no render.yaml