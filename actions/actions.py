import logging
import json
import subprocess
import os
import fitz 
from typing import Any, Text, Dict, List
from datetime import datetime, timedelta

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset, FollowupAction, ActiveLoop
from rasa_sdk.types import DomainDict

import google.generativeai as genai
from dotenv import load_dotenv

import re

import requests 


load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_API_URL = os.getenv("DATABASE_API_URL", "http://localhost:3000")


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("Chave de API do Gemini não encontrada. Verifique seu arquivo .env")
    gemini_model = None
else:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')


class ActionHandleGeneralQuestion(Action):
    """Usa a API do Gemini para responder a perguntas não previstas."""
    def name(self) -> Text:
        return "action_handle_general_question"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        if not gemini_model:
            dispatcher.utter_message(response="utter_default")
            return []

        user_message = tracker.latest_message.get('text')
        
        prompt = f"""
        Você é um assistente virtual de uma clínica chamada "Clínica Super Saudável".
        Sua função primária é agendar consultas. Responda a perguntas gerais sobre saúde de forma prestativa, mas NUNCA forneça diagnósticos.
        Se o usuário perguntar algo que você não sabe ou que pareça um pedido de diagnóstico, guie-o a marcar uma consulta.
        Pergunta do Usuário: "{user_message}"
        Sua Resposta:
        """
        try:
            response = gemini_model.generate_content(prompt)
            dispatcher.utter_message(text=response.text)
        except Exception as e:
            logger.error(f"Erro ao chamar a API do Gemini: {e}")
            dispatcher.utter_message(response="utter_default")
        return []


class ActionExtractInfoWithGemini(Action):
    def name(self) -> Text:
        return "action_extract_info_with_gemini"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        if not gemini_model:
            dispatcher.utter_message(text="Desculpe, estou com problemas técnicos. Vamos tentar de outra forma.")
            return [FollowupAction("formulario_agendamento")]

        user_message = tracker.latest_message.get('text')

        prompt = f"""
        Analise a frase do usuário e extraia as seguintes informações em formato JSON. Se uma informação não estiver presente, use "null".
        Entidades: especialidade, nome_doutor, data_preferida, nome_paciente, email.
        Frase: "{user_message}"
        JSON:
        """
        try:
            response = gemini_model.generate_content(prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            extracted_data = json.loads(cleaned_response)

            slots_to_set = []
            if extracted_data.get("especialidade"):
                slots_to_set.append(SlotSet("especialidade", extracted_data["especialidade"]))
            if extracted_data.get("data_preferida"):
                slots_to_set.append(SlotSet("data_preferida", extracted_data["data_preferida"]))
            if extracted_data.get("nome_doutor"): # New: Set doctor_name if extracted
                slots_to_set.append(SlotSet("doctor_name", extracted_data["nome_doutor"]))
            if extracted_data.get("nome_paciente"): # New: Set nome_paciente if extracted
                slots_to_set.append(SlotSet("nome_paciente", extracted_data["nome_paciente"]))
            if extracted_data.get("email"): # New: Set email if extracted
                slots_to_set.append(SlotSet("email", extracted_data["email"]))
            
            if slots_to_set:
                dispatcher.utter_message(text="Entendi! Vamos iniciar o agendamento com essas informações.")
                return slots_to_set + [FollowupAction("formulario_agendamento")]
            else:
                
                return [FollowupAction("action_handle_general_question")]
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON do Gemini na extração: {e}. Resposta bruta: {response.text}")
            dispatcher.utter_message(text="Desculpe, tive um problema ao processar as informações. Vamos tentar de outra forma.")
            return [FollowupAction("formulario_agendamento")] # Fallback to form for clarity
        except Exception as e:
            logger.error(f"Erro na extração com Gemini: {e}")
            return [FollowupAction("action_handle_general_question")]


def _run_db_service(args: List[str]) -> Any:
    """Executa uma chamada de API para o serviço de banco de dados e retorna a resposta JSON."""
    if not args:
        logger.error("Nenhum argumento fornecido para _run_db_service")
        return None

    action = args[0]
    params = args[1:]
    
    get_endpoints = {
        "getSpecialties": "/specialties",
        "getDoctorsBySpecialty": f"/doctors/specialty/{params[0]}" if params else None,
        "getAvailableSlotsByDoctorAndDate": f"/doctors/{params[0]}/available-slots?date={params[1]}" if len(params) > 1 else None,
    }
    
    post_endpoints = {
        "findOrCreatePatient": "/patients",
        "createAppointment": "/appointments"
    }

    try:
        if action in get_endpoints:
            endpoint = get_endpoints[action]
            if not endpoint:
                raise ValueError(f"Parâmetros faltando para a ação GET: {action}")
            
            url = f"{DATABASE_API_URL}{endpoint}"
            logger.debug(f"Chamando GET: {url}")
            response = requests.get(url, timeout=10) # 10 segundos de timeout

        elif action in post_endpoints:
            endpoint = post_endpoints[action]
            url = f"{DATABASE_API_URL}{endpoint}"
            
            # Converte os dados para o formato JSON correto
            if action == "findOrCreatePatient":
                payload = {"email": params[0], "name": params[1]}
            elif action == "createAppointment":
                # O parâmetro já vem como uma string JSON, então carregamos
                payload = json.loads(params[0])
            else:
                payload = {}

            logger.debug(f"Chamando POST: {url} com dados: {payload}")
            response = requests.post(url, json=payload, timeout=10)

        else:
            logger.error(f"Ação desconhecida para a API: {action}")
            return None

        response.raise_for_status()  # Lança um erro para respostas 4xx/5xx
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de rede ao chamar o serviço de DB: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON da resposta da API: {e}. Resposta: {response.text}")
        return None
    except Exception as e:
        logger.error(f"Um erro inesperado ocorreu em _run_db_service: {e}")
        return None

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



class ActionAskDoctorId(Action):
    def name(self) -> Text:
        return "action_ask_doctor_id"

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
        return []

class ActionAgendarConsulta(Action):
    def name(self) -> Text:
        return "action_agendar_consulta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        patient = _run_db_service(["findOrCreatePatient", tracker.get_slot("email"), tracker.get_slot("nome_paciente")])
        if not patient:
            dispatcher.utter_message(response="utter_erro_agendamento")
            return [AllSlotsReset()]

        data_preferida_str = tracker.get_slot("data_preferida") # Expected format: DD/MM/YYYY
        horario_escolhido = tracker.get_slot("horario_escolhido") # Expected format: HH:MM

        try:
            # Parse the date (DD/MM/YYYY)
            day, month, year_str = data_preferida_str.split('/')

            current_year = datetime.now().year
            parsed_date = datetime(int(year_str), int(month), int(day))
            if parsed_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                parsed_date = datetime(current_year + 1, int(month), int(day))

            # Combine with chosen time
            hora, minuto = map(int, horario_escolhido.split(':'))
            appointment_datetime = parsed_date.replace(hour=hora, minute=minuto, second=0, microsecond=0)

        except Exception as e:
            logger.error(f"Erro ao parsear data ou hora para agendamento: {e}")
            dispatcher.utter_message(response="utter_erro_agendamento")
            return [AllSlotsReset()]

        appointment_data = {
            "patientId": patient['id'],
            "doctorId": int(tracker.get_slot("doctor_id")),
            "dateTime": appointment_datetime.isoformat() + "Z",
        }

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

            return [AllSlotsReset()]
        else:
            dispatcher.utter_message(response="utter_erro_agendamento")
            # Em caso de erro, limpamos os slots para recomeçar.
            return [AllSlotsReset()]


WEEKDAY_MAP = {
    "segunda": 0, "segunda-feira": 0,
    "terça": 1, "terça-feira": 1,
    "quarta": 2, "quarta-feira": 2,
    "quinta": 3, "quinta-feira": 3,
    "sexta": 4, "sexta-feira": 4,
    "sábado": 5,
    "domingo": 6,
}

def _find_next_weekday(start_date: datetime, target_weekday: int) -> datetime:
    """Encontra a data da próxima ocorrência de um dia da semana."""
    days_ahead = target_weekday - start_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


class ValidateFormularioAgendamento(FormValidationAction):
    def name(self) -> Text:
        return "validate_formulario_agendamento"
        
    async def validate_horario_escolhido(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]: # A anotação de tipo foi corrigida para o padrão do Rasa
        """Valida a escolha do horário de forma flexível."""
        horarios_disponiveis = tracker.get_slot("horarios_disponiveis")
        user_text = tracker.latest_message.get("text", "").lower()

        if not horarios_disponiveis:
            dispatcher.utter_message(text="Desculpe, parece que não tenho horários para validar.")
            return {"horario_escolhido": None}

        validated_horario = None

        # 1. Tenta encontrar o horário exato (ex: "15:00")
        for horario in horarios_disponiveis:
            if horario in user_text:
                validated_horario = horario
                break

        if not validated_horario:
            # 2. Tenta encontrar números no texto (ex: "às 9h", "9 horas")
            numeros_encontrados = re.findall(r'\d+', user_text)
            if numeros_encontrados:
                for num_str in numeros_encontrados:
                    for horario in horarios_disponiveis:
                        if horario.startswith(num_str.zfill(2)): # zfill(2) transforma '9' em '09'
                            validated_horario = horario
                            break
                    if validated_horario:
                        break

        if not validated_horario:
            # 3. Tenta encontrar por posição (ex: "o primeiro", "opção 2")
            posicoes = {
                "primeiro": 0, "primeira": 0, "1": 0,
                "segundo": 1, "segunda": 1, "2": 1,
                "terceiro": 2, "terceira": 2, "3": 2,
            }
            for palavra, index in posicoes.items():
                if palavra in user_text:
                    if len(horarios_disponiveis) > index:
                        validated_horario = horarios_disponiveis[index]
                        break

        if validated_horario:
            # Apenas retorna o slot validado. O Rasa cuidará do resto.
            return {"horario_escolhido": validated_horario}
        else:
            dispatcher.utter_message(
                text=f"Não consegui entender sua escolha. Por favor, selecione um dos horários a seguir: {', '.join(horarios_disponiveis)}"
            )
            return {"horario_escolhido": None}


    async def validate_data_preferida(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida a data e busca os horários disponíveis no banco."""
        
        doctor_id = tracker.get_slot("doctor_id")
        doctor_name = tracker.get_slot("doctor_name")
        user_input_date = slot_value.lower()

        if not doctor_id or doctor_id == 'any':
            dispatcher.utter_message(text="Por favor, selecione um médico primeiro.")
            return {"data_preferida": None}

        today = datetime.now()
        target_date = None

        # Try to parse exact date first (DD/MM or DD/MM/YYYY)
        match_date = re.match(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', user_input_date)
        if match_date:
            day, month, year = match_date.groups()
            try:
                if year:
                    year_int = int(year)
                    if len(year) == 2: # Handle 2-digit year (e.g., 24 for 2024)
                        year_int = 2000 + year_int if year_int < 50 else 1900 + year_int
                    target_date = datetime(year_int, int(month), int(day))
                else: # No year specified, assume current year
                    target_date = datetime(today.year, int(month), int(day))
                
                # If date is in the past, try next year
                if target_date < today.replace(hour=0, minute=0, second=0, microsecond=0):
                    target_date = datetime(today.year + 1, int(month), int(day))
            except ValueError:
                pass # Continue to other parsing methods if invalid date

        if not target_date: # If exact date parsing failed, try relative dates
            if "hoje" in user_input_date:
                target_date = today
            elif "amanhã" in user_input_date:
                target_date = today + timedelta(days=1)
            else:
                # Check for weekdays (e.g., "segunda", "terça")
                for day_name, day_index in WEEKDAY_MAP.items():
                    if day_name in user_input_date:
                        target_date = _find_next_weekday(today, day_index)
                        break
        
        if not target_date:
            dispatcher.utter_message(text=f"Não entendi a data '{slot_value}'. Por favor, tente 'hoje', 'amanhã', 'DD/MM' ou um dia da semana como 'segunda'.")
            return {"data_preferida": None}

        # Set time to midday to avoid timezone issues with start/end of day
        target_date = target_date.replace(hour=12, minute=0, second=0, microsecond=0)
        date_iso = target_date.strftime("%Y-%m-%d")

        # Calls the service to fetch available slots
        horarios_disponiveis = _run_db_service(["getAvailableSlotsByDoctorAndDate", str(doctor_id), date_iso])
        
        if horarios_disponiveis is None:
            dispatcher.utter_message(text="Desculpe, tive um problema ao verificar os horários. Tente novamente.")
            return {"data_preferida": None}

        if horarios_disponiveis:
            horarios_str = ", ".join(horarios_disponiveis)
            message = f"Ótimo! Encontrei os seguintes horários para o(a) Dr(a). {doctor_name} no dia {target_date.strftime('%d/%m/%Y')}: {horarios_str}"
            buttons = [{"title": h, "payload": f'/informar_horario_escolhido{{"horario_escolhido":"{h}"}}'} for h in horarios_disponiveis]
            dispatcher.utter_message(text=message, buttons=buttons)
            return {"data_preferida": target_date.strftime('%d/%m/%Y'), "horarios_disponiveis": horarios_disponiveis}
        else:
            dispatcher.utter_message(text=f"Desculpe, o(a) Dr(a). {doctor_name} não tem horários livres no dia {target_date.strftime('%d/%m/%Y')}. Por favor, escolha outra data.")
            return {"data_preferida": None, "horarios_disponiveis": []}

class ActionLerPdfEResponder(Action):
    def name(self) -> Text:
        return "action_ler_pdf_e_responder"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        caminho_pdf = "data/material.pdf"  # ajuste para o caminho real do seu PDF

        try:
            with fitz.open(caminho_pdf) as doc:
                texto = ""
                for pagina in doc:
                    texto += pagina.get_text()

            pergunta_usuario = tracker.latest_message.get("text")

            if not gemini_model:
                dispatcher.utter_message(text="Desculpe, estou com problemas técnicos para processar sua pergunta.")
                return []

            prompt = f"""
            Você é um assistente da Clínica Super Saudável. Responda à pergunta do usuário com base no conteúdo a seguir, retirado de um material PDF:

            --- CONTEÚDO DO MATERIAL ---
            {texto}
            --- FIM DO MATERIAL ---

            Pergunta: "{pergunta_usuario}"
            Resposta:
            """

            resposta = gemini_model.generate_content(prompt)
            dispatcher.utter_message(text=resposta.text)

        except Exception as e:
            logger.error(f"Erro ao processar o PDF: {e}")
            dispatcher.utter_message(text="Desculpe, houve um erro ao acessar o material.")

        return []
