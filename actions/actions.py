from typing import Any, Text, Dict, List
import random
import string

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset, ActiveLoop

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
} }

class ActionBuscarEspecialidades(Action):
    def name(self) -> Text:
        return "action_buscar_especialidades"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if ESPECIALIDADES_DA_CLINICA:
            message = "As especialidades disponíveis são: " + ", ".join(ESPECIALIDADES_DA_CLINICA) + "."
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

        if especialidade and especialidade in EXAMES_POR_ESPECIALIDADE:
            exames_disponiveis = EXAMES_POR_ESPECIALIDADE[especialidade]
            message = f"Para {especialidade}, os exames disponíveis são: {', '.join(exames_disponiveis)}."
            dispatcher.utter_message(text=message)
        elif especialidade:
            message = f"Não encontrei exames específicos para {especialidade} ou essa especialidade não oferece exames diretamente por aqui."
            dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(text="Por favor, informe primeiro a especialidade para que eu possa listar os exames.")
            
        return [SlotSet("exames_disponiveis_para_especialidade", exames_disponiveis)]


class ActionVerificarDisponibilidade(Action):
    def name(self) -> Text:
        return "action_verificar_disponibilidade"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        especialidade = tracker.get_slot("especialidade")
        data_preferida = tracker.get_slot("data_preferida")
        hora_preferida = tracker.get_slot("hora_preferida")

        print(f"Verificando disponibilidade para: {especialidade} em {data_preferida} às {hora_preferida}")

        horarios_encontrados = []
        status = "nenhum"

        if especialidade and data_preferida:
            periodo_desejado = None
            if hora_preferida:
                if "manhã" in hora_preferida.lower():
                    periodo_desejado = "manhã"
                elif "tarde" in hora_preferida.lower():
                    periodo_desejado = "tarde"
            
            if especialidade in HORARIOS_MOCK and data_preferida in HORARIOS_MOCK[especialidade]:
                horarios_do_dia = HORARIOS_MOCK[especialidade][data_preferida]
                
                if periodo_desejado and periodo_desejado in horarios_do_dia:
                    horarios_encontrados = [f"{especialidade} - {data_preferida} - {h}" for h in horarios_do_dia[periodo_desejado]]
                elif not periodo_desejado: # Se não especificou manhã/tarde, mostra todos do dia
                    for p, hs in horarios_do_dia.items():
                        horarios_encontrados.extend([f"{especialidade} - {data_preferida} - {h}" for h in hs])
            
            if horarios_encontrados:
                status = "encontrado"

        if status == "encontrado":
            message = "Horários disponíveis encontrados: " + ", ".join(horarios_encontrados) + ". Qual prefere?"
            dispatcher.utter_message(text=message)
        else:
            msg_part_hora = f" para o período de {hora_preferida}" if hora_preferida else ""
            dispatcher.utter_message(text=f"Desculpe, não há horários disponíveis para {especialidade} em {data_preferida}{msg_part_hora}. Gostaria de tentar outra data/hora?")

        return [SlotSet("horarios_disponiveis", horarios_encontrados), SlotSet("status_disponibilidade", status)]


class ActionAgendarConsulta(Action):
    def name(self) -> Text:
        return "action_agendar_consulta"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        especialidade = tracker.get_slot("especialidade")

        data_confirmada = tracker.get_slot("data_preferida") 
        hora_confirmada = tracker.get_slot("hora_preferida")
        nome_paciente = tracker.get_slot("nome_paciente")

        id_agendamento_gerado = "AG" + "".join(random.choice(string.digits) for _ in range(6))
        status_agendamento = "sucesso"

        print(f"Agendando consulta para {nome_paciente}: {especialidade} em {data_confirmada} as {hora_confirmada}")
        
        if nome_paciente and especialidade and data_confirmada and hora_confirmada:            
            if random.choice([True, False]):
                status_agendamento = "sucesso"
                dispatcher.utter_message(text=f"Agendamento para {nome_paciente} ({especialidade}) no dia {data_confirmada} às {hora_confirmada} realizado com sucesso! Seu ID de agendamento é: {id_agendamento_gerado}.")
            else:
                status_agendamento = "falha"
                dispatcher.utter_message(text="Houve um problema ao realizar o seu agendamento. Por favor, tente novamente mais tarde.")
        else:
            missing_info = []
            if not nome_paciente: missing_info.append("nome do paciente")
            if not especialidade: missing_info.append("especialidade")
            if not data_confirmada: missing_info.append("data")
            if not hora_confirmada: missing_info.append("hora")
            dispatcher.utter_message(text=f"Não consigo completar o agendamento. Faltam informações: {', '.join(missing_info)}.")
            status_agendamento = "falha_dados_insuficientes"


        return [SlotSet("id_agendamento", id_agendamento_gerado if status_agendamento == "sucesso" else None), 
                SlotSet("status_agendamento", status_agendamento)]