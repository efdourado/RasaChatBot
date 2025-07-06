# 1. Usar a imagem oficial do Rasa como base.
FROM rasa/rasa:3.6.10-full

# 2. Copiar todos os arquivos do seu projeto para o diretório de trabalho (/app).
COPY . .

# 3. Mudar para o usuário ROOT para poder instalar pacotes.
USER root

# 4. Instalar as dependências Python para as actions.
#    O --no-cache-dir é uma boa prática para manter a imagem menor.
RUN pip install --no-cache-dir -r actions/requirements.txt

# 5. Treinar o modelo Rasa (ainda como root, que tem permissão de escrita).
RUN rasa train

# 6. Mudar de volta para o usuário padrão e seguro do Rasa.
#    Isso garante que seu aplicativo não execute com privilégios de root.
USER rasa

# O comando para iniciar o serviço será pego do render.yaml