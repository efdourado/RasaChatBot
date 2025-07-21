# import logging
# import json
# import fitz
# import requests
# from typing import Text, Dict, Any

# from rasa_sdk.endpoint import ActionEndpoint
# from rasa_sdk.executor import ActionExecutor
# from rasa_sdk.interfaces import Action
# from sanic import Sanic, response

# from actions.actions import *

# logger = logging.getLogger(__name__)

# # URL do servidor Rasa (usando o nome do serviço do render.yaml)
# # A porta padrão do Rasa é 5005
# RASA_SERVER_URL = "http://chatbot-rasa-server:5005"

# def create_action_app(action_package_name: Text) -> Sanic:
#     """Cria o app Sanic do servidor de ações e adiciona o endpoint de upload."""

#     # Cria o executor de ações padrão do Rasa
#     executor = ActionExecutor()
#     executor.register_package(action_package_name)

#     # Cria o app Sanic
#     app = Sanic("rasa_sdk", configure_logging=False)

#     # Cria o endpoint de ações padrão do Rasa (/webhook)
#     action_endpoint = ActionEndpoint(executor)
#     app.add_route(action_endpoint.health, "/health", methods=["GET", "OPTIONS"])
#     app.add_route(action_endpoint.webhook, "/webhook", methods=["POST", "OPTIONS"])

#     @app.post("/upload-pdf")
#     async def upload_pdf(request):
#         """
#         Recebe um PDF, extrai o texto e o envia para a NLU do Rasa para
#         extrair entidades e disparar a ação de agendamento.
#         """
#         # O frontend deve enviar o `sender_id` para sabermos a qual conversa pertence
#         sender_id = request.form.get("sender_id")
#         if not sender_id:
#             return response.json({"error": "O campo 'sender_id' é obrigatório."}, status=400)

#         # Pega o arquivo PDF do request
#         pdf_file = request.files.get("pdf")
#         if not pdf_file:
#             return response.json({"error": "Nenhum arquivo PDF enviado."}, status=400)

#         try:
#             # Extrai o texto do PDF usando PyMuPDF
#             pdf_document = fitz.open(stream=pdf_file.body, filetype="pdf")
#             extracted_text = ""
#             for page in pdf_document:
#                 extracted_text += page.get_text()

#             logger.info(f"Texto extraído do PDF para sender_id '{sender_id}': {extracted_text[:300]}...")

#             nlu_payload = {"text": extracted_text}
#             nlu_response = requests.post(f"{RASA_SERVER_URL}/model/parse", json=nlu_payload)
#             nlu_response.raise_for_status()
#             nlu_data = nlu_response.json()

#             logger.info(f"Resposta da NLU: {json.dumps(nlu_data, indent=2)}")

#             intent_name = nlu_data.get("intent", {}).get("name")
#             entities = nlu_data.get("entities", [])

#             if not intent_name:
#                 return response.json({"message": "Nenhuma intenção foi identificada no PDF."})

#             trigger_payload = {
#                 "name": intent_name,
#                 "entities": {entity["entity"]: entity["value"] for entity in entities}
#             }

#             trigger_url = f"{RASA_SERVER_URL}/conversations/{sender_id}/trigger_intent"
#             trigger_response = requests.post(trigger_url, json=trigger_payload)
#             trigger_response.raise_for_status()

#             return response.json({
#                 "message": "PDF processado com sucesso. A ação correspondente foi disparada.",
#                 "nlu_result": nlu_data
#             })

#         except Exception as e:
#             logger.error(f"Erro ao processar o PDF: {e}")
#             return response.json({"error": "Falha ao processar o arquivo PDF."}, status=500)

#     return app

# if __name__ == "__main__":
#     app = create_action_app("actions")
#     port = 5055

#     logger.info(f"Servidor de ações customizadas iniciado em http://0.0.0.0:{port}")
#     app.run(host="0.0.0.0", port=port)