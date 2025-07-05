import logging
import json
import subprocess
import os
from typing import Any, Text, Dict, List
from datetime import datetime, timedelta

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk.types import DomainDict


import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv() 

logger = logging.getLogger(__name__)

# --- Configuração do Gemini ---
# Pega a chave da variável de ambiente que configuramos
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("Chave de API do Gemini não encontrada. Verifique seu arquivo .env")
    # Se não houver chave, não podemos continuar a configuração
else:
    genai.configure(api_key=GEMINI_API_KEY)
    # Escolha do modelo. 'gemini-1.5-flash' é rápido e eficiente.
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')

class ActionAskDoctorId(Action):
    def name(self) -> Text:
        return "action_ask_doctor_id"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        especialidade_nome = tracker.get_slot("especialidade")
        if not especialidade_nome:
            # Fallback caso a especialidade não esteja definida
            dispatcher.utter_message(text="Para qual especialidade seria a consulta?")
            return []

        # Busca o ID da especialidade pelo nome
        specialties = _run_db_service(["getSpecialties"])
        if not specialties:
            dispatcher.utter_message(text="Desculpe, estou com problemas para acessar nossas especialidades.")
            return [SlotSet("especialidade", None)]

        selected_specialty = next((s for s in specialties if s['name'].lower() == especialidade_nome.lower()), None)
        if not selected_specialty:
            dispatcher.utter_message(f"Não encontrei a especialidade '{especialidade_nome}'.")
            return [SlotSet("especialidade", None)]

        # Busca doutores pela especialidade e mostra os botões
        doctors = _run_db_service(["getDoctorsBySpecialty", str(selected_specialty['id'])])
        if doctors:
            message = f"Para {especialidade_nome}, temos os seguintes especialistas. Qual deles você prefere?"
            buttons = [{"title": d['name'], "payload": f'/informar_doutor{{"doctor_id":"{d["id"]}", "doctor_name":"{d["name"]}"}}'} for d in doctors]
            buttons.append({"title": "Qualquer um", "payload": '/informar_doutor{"doctor_id":"any"}'})
            
            dispatcher.utter_message(text=message, buttons=buttons)
        else:
            dispatcher.utter_message(f"Não encontrei doutores para {especialidade_nome}. Gostaria de tentar outra especialidade?")
            return [SlotSet("especialidade", None)]
        
        return []


# --- AÇÃO DE FALLBACK COM IA GENERATIVA (VERSÃO COMPLETA) ---
class ActionHandleGeneralQuestion(Action):
    """Usa a API do Gemini para responder a perguntas não previstas."""
    def name(self) -> Text:
        return "action_handle_general_question"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        # Verifica se a API foi configurada corretamente
        if not GEMINI_API_KEY:
            dispatcher.utter_message(response="utter_erro_agendamento") # Resposta genérica de erro
            return []

        # Pega a última mensagem do usuário
        user_message = tracker.latest_message.get('text')
        
        # Pega o histórico da conversa para dar contexto ao Gemini
        conversation_history = []
        for event in tracker.events:
            if event['event'] == 'user':
                conversation_history.append(f"Usuário: {event['text']}")
            elif event['event'] == 'bot':
                # Pega o texto da resposta do bot
                bot_text = event.get('text')
                if bot_text:
                    conversation_history.append(f"Assistente: {bot_text}")

        # Junta o histórico em uma string
        context = "\n".join(conversation_history)

        # --- Engenharia de Prompt: A parte mais importante! ---
        # Damos ao Gemini uma "persona" e instruções claras.
        prompt = f"""
        Você é um assistente virtual de uma clínica chamada "Clínica Super Saudável". Seu nome é Gênio da Saúde.
        Sua função primária é agendar consultas, mas você também pode responder a perguntas gerais sobre saúde de forma prestativa, empática e segura.
        
        **Instruções Importantes:**
        1.  **NUNCA FORNEÇA DIAGNÓSTICOS MÉDICOS.** Se o usuário pedir um diagnóstico, responda de forma educada para ele procurar um médico real. Ex: "Como assistente virtual, não posso fornecer diagnósticos. Recomendo que você agende uma consulta para conversar com um de nossos especialistas."
        2.  **Use o histórico da conversa para entender o contexto.**
        3.  **Seja conciso e direto.**
        4.  **Se a pergunta for sobre agendamento, especialidades ou médicos, guie o usuário para usar os comandos corretos.** Ex: "Parece que você quer marcar uma consulta. Posso iniciar o processo de agendamento para você."

        **Histórico da Conversa:**
        {context}
        
        **Pergunta do Usuário:**
        "{user_message}"

        **Sua Resposta:**
        """

        try:
            logger.info(f"Enviando prompt para o Gemini: {user_message}")
            response = gemini_model.generate_content(prompt)
            
            # Envia a resposta do Gemini diretamente para o usuário
            dispatcher.utter_message(text=response.text)

        except Exception as e:
            logger.error(f"Erro ao chamar a API do Gemini: {e}")
            # Resposta de fallback caso o Gemini falhe
            dispatcher.utter_message(response="utter_default")
            dispatcher.utter_message(response="utter_solicitar_ajuda")

        return []


class ActionExtractInfoWithGemini(Action):
    def name(self) -> Text:
        return "action_extract_info_with_gemini"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        if not GEMINI_API_KEY:
            dispatcher.utter_message(response="utter_erro_agendamento")
            return []

        user_message = tracker.latest_message.get('text')

        prompt = f"""
        Analise a frase do usuário e extraia as seguintes informações em formato JSON. Se uma informação não estiver presente, use "null".
        Entidades a extrair:
        - especialidade (ex: Cardiologia, Dermatologia)
        - nome_doutor (ex: Dr. João, Dra. Ana)
        - data_preferida (ex: amanhã, 25/07, terça-feira)

        Frase do usuário: "{user_message}"

        JSON:
        """
        
        try:
            response = gemini_model.generate_content(prompt)
            # Limpa a resposta para garantir que seja um JSON válido
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            extracted_data = json.loads(cleaned_response)

            slots_to_set = []
            if extracted_data.get("especialidade"):
                slots_to_set.append(SlotSet("especialidade", extracted_data["especialidade"]))
            if extracted_data.get("nome_doutor"):
                # Aqui você precisaria de uma lógica para buscar o ID do doutor pelo nome
                slots_to_set.append(SlotSet("doctor_name", extracted_data["nome_doutor"]))
            if extracted_data.get("data_preferida"):
                slots_to_set.append(SlotSet("data_preferida", extracted_data["data_preferida"]))
            
            # Ativa o formulário de agendamento se alguma informação foi extraída
            if slots_to_set:
                dispatcher.utter_message(text="Entendi! Deixe-me só confirmar alguns dados com você...")
                return slots_to_set + [FollowupAction("formulario_agendamento")]
            else:
                 # Se nada foi extraído, talvez seja uma pergunta geral
                return [FollowupAction("action_handle_general_question")]

        except Exception as e:
            logger.error(f"Erro na extração com Gemini: {e}")
            return [FollowupAction("action_handle_general_question")]







# --- FUNÇÃO AUXILIAR PARA O BANCO DE DADOS ---
def _run_db_service(command: List[str]) -> Any:
    """Executa o serviço de banco de dados e retorna a saída JSON."""
    # Garante que o ts-node seja encontrado localmente no projeto
    base_command = ["./node_modules/.bin/ts-node", "src/service.ts"]
    full_command = base_command + command
    
    try:
        logger.info(f"Executando comando de BD: {' '.join(full_command)}")
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8' # Garante a codificação correta
        )
        # Lida com o caso de não haver saída (ex: reset bem-sucedido)
        if not result.stdout:
            return None
        logger.info(f"Saída do BD: {result.stdout}")
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro no serviço de banco de dados (CalledProcessError): {e}")
        logger.error(f"Stderr: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON do serviço de BD: {e}")
        logger.error(f"Stdout recebido: {result.stdout}")
        return None
    except FileNotFoundError:
        logger.error("Erro: 'ts-node' não encontrado. Certifique-se de que as dependências do Node.js estão instaladas com 'npm install'.")
        return None
    except Exception as e:
        logger.error(f"Um erro inesperado ocorreu ao chamar o serviço de BD: {e}")
        return None

# --- AÇÕES DE BUSCA ---
class ActionBuscarEspecialidades(Action):
    def name(self) -> Text:
        return "action_buscar_especialidades"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        specialties = _run_db_service(["getSpecialties"])
        if specialties:
            message = "Temos as seguintes especialidades:"
            buttons = [{"title": s['name'], "payload": f'/informar_especialidade{{"especialidade":"{s["name"]}"}}'} for s in specialties]
            dispatcher.utter_message(text=message, buttons=buttons)
        else:
            dispatcher.utter_message(text="Desculpe, não consegui carregar as especialidades no momento.")
        return []

class ActionBuscarDoutoresPorEspecialidade(Action):
    def name(self) -> Text:
        return "action_buscar_doutores_por_especialidade"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        especialidade_nome = tracker.get_slot("especialidade")
        if not especialidade_nome:
            dispatcher.utter_message(text="Para qual especialidade seria a consulta?")
            return []

        specialties = _run_db_service(["getSpecialties"])
        if not specialties:
            dispatcher.utter_message(text="Desculpe, estou com problemas para acessar nossas especialidades.")
            return [SlotSet("especialidade", None)]

        selected_specialty = next((s for s in specialties if s['name'].lower() == especialidade_nome.lower()), None)
        if not selected_specialty:
            dispatcher.utter_message(f"Não encontrei a especialidade '{especialidade_nome}'.")
            return [SlotSet("especialidade", None)]

        doctors = _run_db_service(["getDoctorsBySpecialty", str(selected_specialty['id'])])
        if doctors:
            message = f"Para {especialidade_nome}, temos os seguintes especialistas. Qual deles você prefere?"
            buttons = [{"title": d['name'], "payload": f'/informar_doutor{{"doctor_id":"{d["id"]}", "doctor_name":"{d["name"]}"}}'} for d in doctors]
            buttons.append({"title": "Qualquer um", "payload": '/informar_doutor{"doctor_id":"any", "doctor_name":"Qualquer um"}'})
            dispatcher.utter_message(text=message, buttons=buttons)
        else:
            dispatcher.utter_message(f"Não encontrei doutores para {especialidade_nome}. Gostaria de tentar outra especialidade?")
            return [SlotSet("especialidade", None)]
        return []

# --- VALIDAÇÃO DO FORMULÁRIO DE AGENDAMENTO ---
class ValidateFormularioAgendamento(FormValidationAction):
    def name(self) -> Text:
        return "validate_formulario_agendamento"

    async def validate_especialidade(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        specialties = _run_db_service(["getSpecialties"])
        if not specialties:
            dispatcher.utter_message("Desculpe, estou com problemas para acessar nossas especialidades.")
            return {"especialidade": None}
        if any(s['name'].lower() == slot_value.lower() for s in specialties):
            return {"especialidade": slot_value}
        else:
            dispatcher.utter_message(f"Não temos a especialidade '{slot_value}'.")
            await self.action_buscar_especialidades.run(dispatcher, tracker, domain)
            return {"especialidade": None}

    async def validate_doctor_id(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        # Se o usuário clicou em "Qualquer um", o payload será 'any'
        if slot_value == "any":
            especialidade_nome = tracker.get_slot("especialidade")
            specialties = _run_db_service(["getSpecialties"])
            selected_specialty = next((s for s in specialties if s['name'].lower() == especialidade_nome.lower()), None)
            
            if selected_specialty:
                doctors = _run_db_service(["getDoctorsBySpecialty", str(selected_specialty['id'])])
                if doctors:
                    first_doctor = doctors[0]
                    dispatcher.utter_message(text=f"Ok! Seguiremos com o(a) primeiro(a) médico(a) disponível: {first_doctor['name']}.")
                    return {"doctor_id": str(first_doctor['id']), "doctor_name": first_doctor['name']}
            
            dispatcher.utter_message(f"Não encontrei doutores para {especialidade_nome}.")
            return {"doctor_id": None}

        # Se um ID numérico foi passado, significa que o usuário clicou em um médico específico
        if slot_value and slot_value.isdigit():
            # O nome do médico já foi setado pelo payload do botão
            return {"doctor_id": slot_value}

        dispatcher.utter_message("Por favor, selecione um doutor da lista de opções.")
        return {"doctor_id": None}

    async def validate_data_preferida(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        return {"data_preferida": slot_value}

    async def validate_horario_escolhido(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        horarios_disponiveis = tracker.get_slot("horarios_disponiveis")
        if horarios_disponiveis and slot_value in horarios_disponiveis:
            return {"horario_escolhido": slot_value}
        else:
            dispatcher.utter_message(f"O horário '{slot_value}' não está na lista de opções. Por favor, escolha um dos horários que eu mostrei.")
            return {"horario_escolhido": None}
            
# --- AÇÕES DE LÓGICA DO AGENDAMENTO ---
class ActionVerificarDisponibilidade(Action):
    def name(self) -> Text:
        return "action_verificar_disponibilidade"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        doctor_id = tracker.get_slot("doctor_id")
        data_preferida_str = tracker.get_slot("data_preferida")
        doctor_name = tracker.get_slot("doctor_name")
        
        # Lógica simples para converter "amanhã" ou "hoje"
        if data_preferida_str.lower() == "amanhã":
            target_date = datetime.now() + timedelta(days=1)
        else:
            try:
                # Tenta analisar formatos como DD/MM/YYYY ou DD/MM
                target_date = datetime.strptime(data_preferida_str, "%d/%m/%Y")
            except ValueError:
                try:
                    date_obj = datetime.strptime(data_preferida_str, "%d/%m")
                    target_date = date_obj.replace(year=datetime.now().year)
                except ValueError:
                     target_date = datetime.now() # Fallback para hoje

        date_iso = target_date.strftime("%Y-%m-%d")

        # Chama o serviço para buscar agendamentos existentes
        appointments = _run_db_service(["getAppointmentsByDoctor", str(doctor_id), date_iso])
        if appointments is None: # Checa erro na chamada
            dispatcher.utter_message("Desculpe, tive um problema ao verificar os horários. Tente novamente.")
            return []

        # Horários de trabalho (poderia vir do banco de dados no futuro)
        horarios_de_trabalho = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        horarios_agendados = [datetime.fromisoformat(a['dateTime'].replace('Z', '')).strftime("%H:%M") for a in appointments]
        
        horarios_disponiveis = [h for h in horarios_de_trabalho if h not in horarios_agendados]
        
        # Dentro da ação action_verificar_disponibilidade em actions.py

        if horarios_disponiveis:
            # Em vez de uma resposta fixa, peça ao Gemini para criar uma
            horarios_str = ", ".join(horarios_disponiveis)
            prompt = f"Crie uma mensagem amigável informando que os horários a seguir estão disponíveis para {doctor_name} no dia {data_preferida_str}: {horarios_str}. Pergunte qual o usuário prefere."
            
            try:
                response = gemini_model.generate_content(prompt)
                dispatcher.utter_message(text=response.text)
            except: # Se falhar, use a resposta padrão
                dispatcher.utter_message(response="utter_ask_horario_escolhido", 
                                        doctor_name=doctor_name, 
                                        data_preferida=data_preferida_str, 
                                        horarios_disponiveis=horarios_str)

            return [SlotSet("horarios_disponiveis", horarios_disponiveis)]
        else:
            # Mesma lógica para quando não há horários
            prompt = f"Crie uma mensagem empática informando que o(a) {doctor_name} não tem horários livres para a data {data_preferida_str}. Sugira gentilmente tentar outra data."
            # ... chamada ao Gemini ...# Dentro da ação action_verificar_disponibilidade em actions.py

class ActionAgendarConsulta(Action):
    def name(self) -> Text:
        return "action_agendar_consulta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        # Busca paciente ou cria um novo
        patient = _run_db_service(["findOrCreatePatient", tracker.get_slot("email"), tracker.get_slot("nome_paciente")])
        if not patient:
            dispatcher.utter_message(response="utter_erro_agendamento")
            return [AllSlotsReset()]

        # Monta o objeto de data e hora do agendamento
        data_preferida_str = tracker.get_slot("data_preferida")
        if data_preferida_str.lower() == "amanhã":
            target_date = datetime.now() + timedelta(days=1)
        else:
            target_date = datetime.now()

        hora, minuto = map(int, tracker.get_slot("horario_escolhido").split(':'))
        appointment_datetime = target_date.replace(hour=hora, minute=minuto, second=0, microsecond=0)

        # Monta os dados para criar o agendamento
        appointment_data = {
            "patientId": patient['id'],
            "doctorId": int(tracker.get_slot("doctor_id")),
            "dateTime": appointment_datetime.isoformat() + "Z", # Formato ISO 8601 com UTC
        }

        # Chama o serviço para criar o agendamento
        final_appointment = _run_db_service(["createAppointment", json.dumps(appointment_data)])

        if final_appointment and final_appointment.get('id'):
            dispatcher.utter_message(
                response="utter_confirmacao_agendamento",
                doctor_name=tracker.get_slot('doctor_name'),
                especialidade=tracker.get_slot('especialidade'),
                data_preferida=appointment_datetime.strftime('%d/%m/%Y'),
                horario_escolhido=tracker.get_slot('horario_escolhido'),
                agendamento_id=final_appointment['id']
            )
        else:
            dispatcher.utter_message(response="utter_erro_agendamento")
            
        return [AllSlotsReset()]

# --- AÇÃO DE FALLBACK COM IA GENERATIVA ---
class ActionHandleGeneralQuestion(Action):
    """Usa uma API de IA Generativa para responder perguntas não previstas."""
    def name(self) -> Text:
        return "action_handle_general_question"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        # Lembre-se de configurar sua chave de API como variável de ambiente (ex: GEMINI_API_KEY)
        # E de instalar a biblioteca necessária (ex: pip install google-generativeai)
        # A lógica para chamar a API do Gemini iria aqui.
        
        # Como placeholder, usamos uma resposta padrão.
        dispatcher.utter_message(response="utter_default")
        dispatcher.utter_message(response="utter_solicitar_ajuda")
        return []