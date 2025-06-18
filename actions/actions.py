import logging
import json
import subprocess

import os

from typing import Any, Text, Dict, List
from datetime import datetime, timedelta

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset

logger = logging.getLogger(__name__)

def _run_db_service(command: List[str]) -> Any:
    """Executa o serviço de banco de dados e retorna a saída JSON."""
    base_command = ["./node_modules/.bin/ts-node", "src/service.ts"]
    full_command = base_command + command
    
    try:
        logger.info(f"Executando comando de BD: {' '.join(full_command)}")
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        logger.info(f"Saída do BD: {result.stdout}")
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Erro ao executar o serviço de banco de dados: {e}")
        if isinstance(e, subprocess.CalledProcessError):
            logger.error(f"Stderr: {e.stderr}")
        return None


class ActionBuscarEspecialidades(Action):
    def name(self) -> Text:
        return "action_buscar_especialidades"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        specialties = _run_db_service(["getSpecialties"])
        
        if specialties:
            specialty_names = [s['name'] for s in specialties]
            dispatcher.utter_message(text=f"As especialidades disponíveis são: {', '.join(specialty_names)}.")
            
            buttons = [{"title": s['name'], "payload": f'/informar_especialidade{{"especialidade":"{s["name"]}"}}'} for s in specialties]
            dispatcher.utter_message(text="Para qual delas você gostaria de agendar?", buttons=buttons)
        else:
            dispatcher.utter_message(text="Desculpe, não consegui buscar as especialidades no momento.")
            
        return []

class ActionBuscarDoutoresPorEspecialidade(Action):
    def name(self) -> Text:
        return "action_buscar_doutores_por_especialidade"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        especialidade_nome = tracker.get_slot("especialidade")
        
        specialties = _run_db_service(["getSpecialties"])
        if not specialties:
            dispatcher.utter_message("Não consegui encontrar nossas especialidades.")
            return []

        selected_specialty = next((s for s in specialties if s['name'].lower() == especialidade_nome.lower()), None)

        if not selected_specialty:
            dispatcher.utter_message(f"Não encontrei a especialidade '{especialidade_nome}'.")
            return []

        doctors = _run_db_service(["getDoctorsBySpecialty", str(selected_specialty['id'])])
        
        if doctors:
            doctor_names = [d['name'] for d in doctors]
            dispatcher.utter_message(text=f"Para {especialidade_nome}, temos os seguintes doutores: {', '.join(doctor_names)}.")
            
            buttons = [{"title": d['name'], "payload": f'/informar_doutor{{"doctor_id":"{d["id"]}", "doctor_name":"{d["name"]}"}}'} for d in doctors]
            dispatcher.utter_message(text="Qual deles você prefere?", buttons=buttons)
        else:
            dispatcher.utter_message(text=f"Não encontrei doutores disponíveis para {especialidade_nome} no momento.")
            
        return []

class ActionVerificarDisponibilidade(Action):
    def name(self) -> Text:
        return "action_verificar_disponibilidade"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        doctor_id = tracker.get_slot("doctor_id")
        data_preferida_str = tracker.get_slot("data_preferida")
        
        if data_preferida_str == "amanhã":
            target_date = datetime.now() + timedelta(days=1)
        else:
            target_date = datetime.now()

        date_iso = target_date.strftime("%Y-%m-%d")

        appointments = _run_db_service(["getAppointmentsByDoctor", str(doctor_id), date_iso])

        horarios_de_trabalho = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
        horarios_agendados = [datetime.fromisoformat(a['dateTime'].replace('Z', '')).strftime("%H:%M") for a in appointments]
        
        horarios_disponiveis = [h for h in horarios_de_trabalho if h not in horarios_agendados]
        
        if horarios_disponiveis:
            dispatcher.utter_message(f"Encontrei estes horários para o dia {target_date.strftime('%d/%m')}: {', '.join(horarios_disponiveis)}")
            return [SlotSet("horarios_disponiveis", horarios_disponiveis)]
        else:
            dispatcher.utter_message(f"Desculpe, não há horários disponíveis para a data selecionada.")
            return [SlotSet("horarios_disponiveis", [])]

class ActionAgendarConsulta(Action):
    def name(self) -> Text:
        return "action_agendar_consulta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        email = tracker.get_slot("email")
        nome_paciente = tracker.get_slot("nome_paciente")
        
        patient = _run_db_service(["findOrCreatePatient", email, nome_paciente])
        if not patient:
            dispatcher.utter_message("Desculpe, tive um problema ao verificar seus dados de paciente.")
            return []

        doctor_id = int(tracker.get_slot("doctor_id"))
        horario_escolhido = tracker.get_slot("horario_escolhido")
        data_preferida_str = tracker.get_slot("data_preferida")
        
        if data_preferida_str == "amanhã":
            target_date = datetime.now() + timedelta(days=1)
        else:
            target_date = datetime.now()
        
        hora, minuto = map(int, horario_escolhido.split(':'))
        appointment_datetime = target_date.replace(hour=hora, minute=minuto, second=0, microsecond=0)

        appointment_data = {
            "patientId": patient['id'],
            "doctorId": doctor_id,
            "dateTime": appointment_datetime.isoformat() + "Z",
            "patientName": patient['name']
        }

        final_appointment = _run_db_service(["createAppointment", json.dumps(appointment_data)])

        if final_appointment:
            dispatcher.utter_message(
                f"Perfeito, {patient['name']}! Sua consulta com {tracker.get_slot('doctor_name')} "
                f"foi agendada para {appointment_datetime.strftime('%d/%m/%Y às %H:%M')}. "
                f"O ID do agendamento é {final_appointment['id']}."
            )
        else:
            dispatcher.utter_message("Desculpe, ocorreu um erro e não consegui finalizar seu agendamento.")
            
        return [AllSlotsReset()]




class ActionBuscarInfoClinica(Action):
    def name(self) -> Text:
        return "action_buscar_info_clinica"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        logger.info("ActionBuscarInfoClinica foi chamada.")

        dispatcher.utter_message(response="utter_info_clinica_placeholder")
        return []


class ActionResetarSlotsAgendamento(Action):
    """Resets slots related to the appointment booking process."""
    def name(self) -> Text:
        return "action_resetar_slots_agendamento"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        logger.info("Resetando slots de agendamento.")
        return [
            SlotSet("especialidade", None),
            SlotSet("data_preferida", None),
            SlotSet("hora_preferida", None),
            SlotSet("nome_paciente", None),
            SlotSet("horarios_disponiveis", None),
            SlotSet("status_disponibilidade", None),
            SlotSet("horario_escolhido", None),
            SlotSet("id_agendamento", None),
            SlotSet("status_agendamento", None)
        ]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class ActionHandleGeneralQuestion(Action):
    """
    Esta ação é acionada quando o chatbot não entende a intenção do usuário.
    Ela usa a API do Gemini para gerar uma resposta para perguntas abertas.
    """
    def name(self) -> Text:
        return "action_handle_general_question"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if not GEMINI_API_KEY:
            logger.error("API Key do Gemini não foi configurada.")
            dispatcher.utter_message(text="Desculpe, meu cérebro de IA avançada está temporariamente offline. Não consigo responder perguntas gerais agora.")
            return []

        
        user_question = tracker.latest_message.get('text')
        logger.info(f"Enviando pergunta para o Gemini: '{user_question}'")

        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
        Você é um assistente virtual de uma clínica chamada 'Clínica Super Saudável'.
        Sua principal função é agendar consultas. No entanto, um usuário fez uma pergunta geral.
        Responda à seguinte pergunta de forma útil e concisa.
        IMPORTANTE: NÃO forneça conselhos médicos. Se a pergunta parecer pedir um diagnóstico ou tratamento, 
        gentilmente instrua o usuário a marcar uma consulta com um de nossos especialistas para obter ajuda profissional.

        Pergunta do usuário: "{user_question}"
        """

        try:
            response = model.generate_content(prompt)
            
            dispatcher.utter_message(text=response.text)

        except Exception as e:
            logger.error(f"Erro ao chamar a API do Gemini: {e}")
            dispatcher.utter_message(text="Desculpe, tive um problema ao processar sua pergunta. Poderia tentar de novo?")

        return []
    
class ActionExtractAppointmentInfo(Action):
    """
    Usa o Gemini para extrair entidades (nome, especialidade)
    de uma forma mais robusta que o NLU tradicional.
    """
    def name(self) -> Text:
        return "action_extract_appointment_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_message = tracker.latest_message.get('text')
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
        Analise a frase de um usuário que deseja marcar uma consulta.
        Extraia o nome do paciente e a especialidade médica desejada.
        Responda APENAS com um objeto JSON válido contendo as chaves 'nome_paciente' e 'especialidade'.
        Se uma informação não for encontrada, use o valor null.

        Frase do usuário: "{user_message}"

        JSON:
        """

        try:
            response = model.generate_content(prompt)
           
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            extracted_data = json.loads(cleaned_response)

            logger.info(f"Dados extraídos pelo Gemini: {extracted_data}")

            slots_to_set = []
            if extracted_data.get("nome_paciente"):
                slots_to_set.append(SlotSet("nome_paciente", extracted_data["nome_paciente"]))
            if extracted_data.get("especialidade"):
                slots_to_set.append(SlotSet("especialidade_desejada", extracted_data["especialidade"]))

            return slots_to_set

        except Exception as e:
            logger.error(f"Erro ao extrair informações com o Gemini: {e}")
            dispatcher.utter_message(text="Não consegui entender todos os detalhes. Pode me dizer seu nome e a especialidade que deseja?")
            return []