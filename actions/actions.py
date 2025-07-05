import logging
import json
import subprocess
import os
from typing import Any, Text, Dict, List
from datetime import datetime, timedelta

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset, FollowupAction
from rasa_sdk.types import DomainDict

import google.generativeai as genai
from dotenv import load_dotenv

import re

load_dotenv()

logger = logging.getLogger(__name__)


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
        Entidades: especialidade, nome_doutor, data_preferida.
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
            
            if slots_to_set:
                dispatcher.utter_message(text="Entendi! Vamos iniciar o agendamento com essas informações.")
                return slots_to_set + [FollowupAction("formulario_agendamento")]
            else:
                return [FollowupAction("action_handle_general_question")]
        except Exception as e:
            logger.error(f"Erro na extração com Gemini: {e}")
            return [FollowupAction("action_handle_general_question")]


def _run_db_service(args: List[str]) -> Any:
    """Executa o script de serviço do banco de dados e retorna a saída JSON."""
    try:
        command = ["npx", "ts-node", "src/service.ts"] + args
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )

        json_output = None
        for line in result.stdout.strip().split('\n'):
            if line.startswith('[') or line.startswith('{'):
                json_output = line
                break
        
        if json_output:
            return json.loads(json_output)
        
        print("Saída do serviço não continha JSON:", result.stdout)
        return None

    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o serviço: {e}")
        print("Stderr:", e.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {e}")
        return None
    except Exception as e:
        print(f"Um erro inesperado ocorreu: {e}")
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






class ActionVerificarDisponibilidade(Action):
    def name(self) -> Text:
        return "action_verificar_disponibilidade"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        doctor_id = tracker.get_slot("doctor_id")
        data_preferida_str = tracker.get_slot("data_preferida")
        doctor_name = tracker.get_slot("doctor_name")

        # ... (lógica para escolher doutor 'any' permanece a mesma) ...
        # ...

        # Lógica para converter "amanhã", "hoje", etc.
        target_date = datetime.now()
        if "amanhã" in data_preferida_str.lower():
            target_date += timedelta(days=1)
        
        # Formata a data para YYYY-MM-DD, que é o que o service.ts espera
        date_iso = target_date.strftime("%Y-%m-%d")
        
        # 1. Horários de trabalho ESTÁTICOS (como você mencionou)
        horarios_de_trabalho = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        
        # 2. Busca os agendamentos existentes no banco de dados para a data
        # A chamada está correta: nome da função, id do médico, e a data formatada
        appointments = _run_db_service(["getAppointmentsByDoctorAndDate", doctor_id, date_iso])
        
        if appointments is None:
            dispatcher.utter_message("Desculpe, tive um problema ao verificar os horários. Poderia tentar novamente?")
            return []

        # 3. Extrai apenas a HORA dos agendamentos existentes
        horarios_agendados = [datetime.fromisoformat(a['dateTime'].replace('Z', '')).strftime("%H:%M") for a in appointments]
        
        # 4. Calcula os horários realmente disponíveis
        horarios_disponiveis = [h for h in horarios_de_trabalho if h not in horarios_agendados]

        if horarios_disponiveis:
            message = f"Encontrei os seguintes horários disponíveis para o(a) Dr(a). {doctor_name} no dia {target_date.strftime('%d/%m')}:"
            buttons = [{"title": h, "payload": f'/informar_horario_escolhido{{"horario_escolhido":"{h}"}}'} for h in horarios_disponiveis]
            dispatcher.utter_message(text=message, buttons=buttons)
            return [SlotSet("horarios_disponiveis", horarios_disponiveis)]
        else:
            dispatcher.utter_message(f"Desculpe, o(a) Dr(a). {doctor_name} não tem horários livres na data solicitada. Gostaria de tentar outra data?")
            return [SlotSet("data_preferida", None), SlotSet("horarios_disponiveis", [])]


class ActionAgendarConsulta(Action):
    def name(self) -> Text:
        return "action_agendar_consulta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        patient = _run_db_service(["findOrCreatePatient", tracker.get_slot("email"), tracker.get_slot("nome_paciente")])
        if not patient:
            dispatcher.utter_message(response="utter_erro_agendamento")
            return [AllSlotsReset()]

        data_str = tracker.get_slot("data_preferida")
        # CORREÇÃO: Usa o slot correto para pegar o horário
        horario_escolhido = tracker.get_slot("horario_escolhido") 

        target_date = datetime.now()
        if "amanhã" in data_str.lower():
            target_date += timedelta(days=1)
            
        # CORREÇÃO: Garante que 'horario_escolhido' não seja nulo antes de usar
        if not horario_escolhido:
            dispatcher.utter_message("Ocorreu um erro, não consegui identificar o horário escolhido. Vamos tentar novamente.")
            return [AllSlotsReset()]

        hora, minuto = map(int, horario_escolhido.split(':'))
        appointment_datetime = target_date.replace(hour=hora, minute=minuto, second=0, microsecond=0)

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
        else:
            dispatcher.utter_message(response="utter_erro_agendamento")
            
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
    ) -> Dict[Text, Any]:
        """Valida a escolha do horário de forma flexível."""
        horarios_disponiveis = tracker.get_slot("horarios_disponiveis")
        user_text = tracker.latest_message.get("text", "").lower()

        if not horarios_disponiveis:
            # Caso de segurança, não deveria acontecer
            dispatcher.utter_message(text="Desculpe, parece que não tenho horários para validar.")
            return {"horario_escolhido": None}

        # 1. Tenta encontrar o horário exato (ex: "15:00")
        for horario in horarios_disponiveis:
            if horario in user_text:
                return {"horario_escolhido": horario}

        # 2. Tenta encontrar números no texto (ex: "às 9h", "9 horas")
        numeros_encontrados = re.findall(r'\d+', user_text)
        if numeros_encontrados:
            for num_str in numeros_encontrados:
                # Procura por horários que comecem com o número encontrado (ex: "9" em "09:00")
                for horario in horarios_disponiveis:
                    if horario.startswith(num_str.zfill(2)): # zfill(2) transforma '9' em '09'
                        return {"horario_escolhido": horario}

        # 3. Tenta encontrar por posição (ex: "o primeiro", "opção 2")
        posicoes = {
            "primeiro": 0, "primeira": 0, "1": 0,
            "segundo": 1, "segunda": 1, "2": 1,
            "terceiro": 2, "terceira": 2, "3": 2,
        }
        for palavra, index in posicoes.items():
            if palavra in user_text:
                if len(horarios_disponiveis) > index:
                    return {"horario_escolhido": horarios_disponiveis[index]}

        # Se nada funcionar, pede para o usuário tentar de novo
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

        # Lógica de conversão de data melhorada
        today = datetime.now()
        target_date = None

        if "hoje" in user_input_date:
            target_date = today
        elif "amanhã" in user_input_date:
            target_date = today + timedelta(days=1)
        elif "/" in user_input_date:
            try:
                day, month = map(int, user_input_date.split('/'))
                target_date = datetime(today.year, month, day)
                if target_date < today.replace(hour=0, minute=0, second=0, microsecond=0):
                    target_date = datetime(today.year + 1, month, day) # Se for no passado, tenta o próximo ano
            except ValueError:
                dispatcher.utter_message(text="Formato de data inválido. Use 'hoje', 'amanhã' ou 'DD/MM'.")
                return {"data_preferida": None}
        else:
            # Verifica se o input é um dia da semana
            for day_name, day_index in WEEKDAY_MAP.items():
                if day_name in user_input_date:
                    target_date = _find_next_weekday(today, day_index)
                    break
        
        if not target_date:
            dispatcher.utter_message(text=f"Não entendi a data '{slot_value}'. Por favor, tente 'hoje', 'amanhã', 'DD/MM' ou um dia da semana como 'segunda'.")
            return {"data_preferida": None}

        date_iso = target_date.strftime("%Y-%m-%d")

        # Chama o serviço para buscar horários disponíveis
        horarios_disponiveis = _run_db_service(["getAvailableSlotsByDoctorAndDate", str(doctor_id), date_iso])
        
        if horarios_disponiveis is None:
            dispatcher.utter_message(text="Desculpe, tive um problema ao verificar os horários. Tente novamente.")
            return {"data_preferida": None}

        if horarios_disponiveis:
            horarios_str = ", ".join(horarios_disponiveis)
            message = f"Ótimo! Encontrei os seguintes horários para o(a) Dr(a). {doctor_name} no dia {target_date.strftime('%d/%m')}: {horarios_str}"
            buttons = [{"title": h, "payload": f'/informar_horario_escolhido{{"horario_escolhido":"{h}"}}'} for h in horarios_disponiveis]
            dispatcher.utter_message(text=message, buttons=buttons)
            return {"data_preferida": target_date.strftime('%d/%m/%Y'), "horarios_disponiveis": horarios_disponiveis}
        else:
            dispatcher.utter_message(text=f"Desculpe, o(a) Dr(a). {doctor_name} não tem horários livres no dia {target_date.strftime('%d/%m')}. Por favor, escolha outra data.")
            return {"data_preferida": None, "horarios_disponiveis": []}