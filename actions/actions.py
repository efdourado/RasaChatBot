import logging
from typing import Any, Text, Dict, List
import random
import string

import os
import google.generativeai as genai

import json

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset

logger = logging.getLogger(__name__)

ESPECIALIDADES_DA_CLINICA = ["Cardiologia", "Dermatologia", "Ortopedia", "Pediatria", "Clínico Geral"]
EXAMES_POR_ESPECIALIDADE = {
    "Cardiologia": ["Eletrocardiograma", "Ecocardiograma", "Teste Ergométrico"],
    "Dermatologia": ["Biópsia de Pele", "Dermatoscopia"],
    "Ortopedia": ["Raio-X", "Ressonância Magnética"],
    "Pediatria": ["Teste do Pezinho", "Triagem Auditiva Neonatal"],
    "Clínico Geral": ["Hemograma Completo", "Exame de Urina"]
}

HORARIOS_MOCK = {
    "Cardiologia": {
        "hoje": {"manhã": ["09:00", "10:30"], "tarde": ["14:00", "15:30"]},
        "amanhã": {"manhã": ["09:30", "11:00"], "tarde": ["14:30", "16:00"]},
    },
    "Dermatologia": {
        "hoje": {"tarde": ["14:15", "16:15"]},
        "amanhã": {"manhã": ["08:00", "09:45"], "tarde": ["13:00"]},
    },
    "Ortopedia": {
        "hoje": {"manhã": ["08:30", "10:00"], "tarde": ["13:30", "15:00"]},
        "amanhã": {"manhã": ["09:00", "10:45"], "tarde": ["14:15", "16:30"]},
    },
    "Pediatria": {
        "hoje": {"manhã": ["09:15"], "tarde": ["14:45", "16:00"]},
        "amanhã": {"tarde": ["13:30", "15:15"]},
    },
    "Clínico Geral": {
        "hoje": {"manhã": ["08:00", "11:30"], "tarde": ["13:00", "16:30"]},
        "amanhã": {"manhã": ["08:30", "10:30"], "tarde": ["14:00", "15:45"]},
} }

class ActionBuscarEspecialidades(Action):
    def name(self) -> Text:
        return "action_buscar_especialidades"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if ESPECIALIDADES_DA_CLINICA:
            message = "As especialidades disponíveis na clínica são: " + ", ".join(ESPECIALIDADES_DA_CLINICA) + "."
            dispatcher.utter_message(text=message)
            return [SlotSet("especialidades_disponiveis", ESPECIALIDADES_DA_CLINICA)]
        else:
            dispatcher.utter_message(text="No momento, não tenho a lista de especialidades. Por favor, tente mais tarde.")
            return [SlotSet("especialidades_disponiveis", [])]


class ActionBuscarExamesPorEspecialidade(Action):
    def name(self) -> Text:
        return "action_buscar_exames_por_especialidade"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        especialidade = tracker.get_slot("especialidade")
        exames_disponiveis = []

        if especialidade:
            if especialidade in EXAMES_POR_ESPECIALIDADE:
                exames_disponiveis = EXAMES_POR_ESPECIALIDADE[especialidade]
                message = f"Para {especialidade}, os exames disponíveis são: {', '.join(exames_disponiveis)}."
                dispatcher.utter_message(text=message)
            else:
                message = f"Não encontrei a especialidade {especialidade} ou ela não possui exames listados por aqui. Gostaria de ver as especialidades que temos?"
                dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(response="utter_perguntar_especialidade_para_exames")
            
        return [SlotSet("exames_disponiveis_para_especialidade", exames_disponiveis if exames_disponiveis else None)]


class ActionVerificarDisponibilidade(Action):
    def name(self) -> Text:
        return "action_verificar_disponibilidade"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        especialidade = tracker.get_slot("especialidade")
        data_preferida = tracker.get_slot("data_preferida")
        hora_preferida = tracker.get_slot("hora_preferida")

        logger.info(f"Verificando disponibilidade para: {especialidade} em {data_preferida} (preferência: {hora_preferida})")

        horarios_encontrados_list = []
        status = "nenhum"

        if not especialidade or not data_preferida:
            dispatcher.utter_message(text="Preciso da especialidade e da data para verificar os horários.")

            return [SlotSet("status_disponibilidade", "dados_insuficientes_verificacao"), SlotSet("horarios_disponiveis", [])]

        if especialidade not in HORARIOS_MOCK:
            logger.warning(f"Especialidade '{especialidade}' não encontrada no HORARIOS_MOCK.")
            dispatcher.utter_message(response="utter_especialidade_nao_encontrada_disponibilidade", especialidade=especialidade)
            return [SlotSet("status_disponibilidade", "especialidade_nao_encontrada"), SlotSet("horarios_disponiveis", [])]

        if data_preferida not in HORARIOS_MOCK[especialidade]:
            logger.info(f"Data '{data_preferida}' não encontrada para '{especialidade}' no HORARIOS_MOCK.")
        else:
            horarios_do_dia_por_periodo = HORARIOS_MOCK[especialidade][data_preferida]
            
            periodo_desejado_str = None
            hora_especifica_desejada = None

            if hora_preferida:
                if "manhã" in hora_preferida.lower():
                    periodo_desejado_str = "manhã"
                elif "tarde" in hora_preferida.lower():
                    periodo_desejado_str = "tarde"
                elif ":" in hora_preferida:
                    hora_especifica_desejada = hora_preferida

            if hora_especifica_desejada:
                for periodo, horarios_no_periodo in horarios_do_dia_por_periodo.items():
                    if hora_especifica_desejada in horarios_no_periodo:
                        horarios_encontrados_list.append(hora_especifica_desejada)
                        break
            elif periodo_desejado_str:
                if periodo_desejado_str in horarios_do_dia_por_periodo:
                    horarios_encontrados_list.extend(horarios_do_dia_por_periodo[periodo_desejado_str])
            else:
                for periodo, horarios_no_periodo in horarios_do_dia_por_periodo.items():
                    horarios_encontrados_list.extend(horarios_no_periodo)
        
        if horarios_encontrados_list:
            status = "encontrado"
           
        else:
            status = "nenhum"

        logger.info(f"Horários encontrados: {horarios_encontrados_list}, Status: {status}")
        return [SlotSet("horarios_disponiveis", horarios_encontrados_list if horarios_encontrados_list else None), SlotSet("status_disponibilidade", status)]


class ActionValidarHorarioEscolhido(Action):
    def name(self) -> Text:
        return "action_validar_horario_escolhido"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        horario_input_usuario = tracker.get_slot("hora_preferida") 

        horario_escolhido_slot_value = tracker.get_slot("horario_escolhido")
        horarios_disponiveis_lista = tracker.get_slot("horarios_disponiveis")

        valid_choice = False
        chosen_time_for_slot = None

        if horario_escolhido_slot_value and horarios_disponiveis_lista:
            if horario_escolhido_slot_value in horarios_disponiveis_lista:
                valid_choice = True
                chosen_time_for_slot = horario_escolhido_slot_value
            else:
                for option in horarios_disponiveis_lista:
                    if option in horario_escolhido_slot_value:
                        valid_choice = True
                        chosen_time_for_slot = option
                        break
        
        if valid_choice:
            logger.info(f"Horário '{chosen_time_for_slot}' validado e escolhido pelo usuário.")
       
            return [SlotSet("horario_escolhido", chosen_time_for_slot)]
        else:
            logger.warning(f"Tentativa de escolha de horário inválido: '{horario_escolhido_slot_value}'. Opções eram: {horarios_disponiveis_lista}")
            dispatcher.utter_message(text=f"Hum, não consegui confirmar o horário '{horario_escolhido_slot_value}'. Por favor, escolha um dos horários que mencionei: {', '.join(horarios_disponiveis_lista) if horarios_disponiveis_lista else 'Nenhum horário disponível para escolher.'}")
            dispatcher.utter_message(response="utter_perguntar_horario_escolhido")
            return [SlotSet("horario_escolhido", None)]

class ActionAgendarConsulta(Action):
    def name(self) -> Text:
        return "action_agendar_consulta"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        especialidade = tracker.get_slot("especialidade")
        data_preferida = tracker.get_slot("data_preferida")
        horario_escolhido = tracker.get_slot("horario_escolhido")
        nome_paciente = tracker.get_slot("nome_paciente")

        id_agendamento_gerado = None
        status_agendamento = "falha_dados_insuficientes"
        informacao_faltante_list = []

        if not nome_paciente: informacao_faltante_list.append("nome do paciente")
        if not especialidade: informacao_faltante_list.append("especialidade")
        if not data_preferida: informacao_faltante_list.append("data")
        if not horario_escolhido: informacao_faltante_list.append("horário confirmado")

        if not informacao_faltante_list:
            logger.info(f"Tentando agendar consulta para {nome_paciente}: {especialidade} em {data_preferida} às {horario_escolhido}")
            
            if random.choice([True, True, False]):
                id_agendamento_gerado = "AG" + "".join(random.choice(string.digits) for _ in range(6))
                status_agendamento = "sucesso"
                logger.info(f"Agendamento para {nome_paciente} bem-sucedido. ID: {id_agendamento_gerado}")
                dispatcher.utter_message(
                    response="utter_agendamento_realizado_com_id", 
                    nome_paciente=nome_paciente, 
                    especialidade=especialidade, 
                    data_preferida=data_preferida, 
                    horario_escolhido=horario_escolhido,
                    id_agendamento=id_agendamento_gerado
                )
            else:
                status_agendamento = "falha_sistema"
                logger.error(f"Falha simulada ao agendar para {nome_paciente}.")
                dispatcher.utter_message(
                    response="utter_agendamento_falhou",
                    nome_paciente=nome_paciente,
                    especialidade=especialidade, 
                    data_preferida=data_preferida, 
                    horario_escolhido=horario_escolhido
                )
        else:
            logger.warning(f"Dados insuficientes para agendamento: {', '.join(informacao_faltante_list)}")
            dispatcher.utter_message(
                response="utter_agendamento_dados_insuficientes", 
                informacao_faltante=", ".join(informacao_faltante_list)
            )

        return [
            SlotSet("id_agendamento", id_agendamento_gerado if status_agendamento == "sucesso" else None), 
            SlotSet("status_agendamento", status_agendamento)
        ]


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

        # Cria o modelo GenerativeModel
        model = genai.GenerativeModel('gemini-pro')

        # Constrói um prompt melhor para dar contexto ao LLM
        prompt = f"""
        Você é um assistente virtual de uma clínica chamada 'Clínica Super Saudável'.
        Sua principal função é agendar consultas. No entanto, um usuário fez uma pergunta geral.
        Responda à seguinte pergunta de forma útil e concisa.
        IMPORTANTE: NÃO forneça conselhos médicos. Se a pergunta parecer pedir um diagnóstico ou tratamento, 
        gentilmente instrua o usuário a marcar uma consulta com um de nossos especialistas para obter ajuda profissional.

        Pergunta do usuário: "{user_question}"
        """

        try:
            # Gera a resposta com o Gemini
            response = model.generate_content(prompt)
            
            # Envia a resposta do Gemini para o usuário
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

        # Este prompt instrui o LLM a agir como um extrator de dados
        # e a responder em um formato de máquina (JSON).
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
            # O Gemini vai responder algo como: ```json\n{"nome_paciente": "João da Silva", "especialidade": "Cardiologia"}\n```
            # Precisamos limpar e parsear essa resposta.
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            extracted_data = json.loads(cleaned_response)

            logger.info(f"Dados extraídos pelo Gemini: {extracted_data}")

            # Agora, preenchemos os slots do Rasa com a informação extraída pelo LLM
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