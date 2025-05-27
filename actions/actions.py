from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset, ActiveLoop

class ActionBuscarEspecialidades(Action):
    def name(self) -> Text:
        return "action_buscar_especialidades"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        especialidades_disponiveis_da_clinica = ["Cardiologia", "Dermatologia", "Ortopedia", "Pediatria", "Clínico Geral"]

        if especialidades_disponiveis_da_clinica:
            message = "As especialidades disponíveis são: " + ", ".join(especialidades_disponiveis_da_clinica) + "."
            dispatcher.utter_message(text=message)
            return [SlotSet("especialidades_disponiveis", especialidades_disponiveis_da_clinica)]
        else:
            dispatcher.utter_message(text="No momento, não tenho a lista de especialidades. Por favor, tente mais tarde.")
            return [SlotSet("especialidades_disponiveis", [])]

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
            if "manhã" in hora_preferida.lower() if hora_preferida else True:
                 horarios_encontrados = [f"{especialidade} - {data_preferida} - 09:00", f"{especialidade} - {data_preferida} - 10:30"]
                 status = "encontrado"
            else:
                 horarios_encontrados = [f"{especialidade} - {data_preferida} - 14:00", f"{especialidade} - {data_preferida} - 15:30"]
                 status = "encontrado"

        if status == "encontrado":
            message = "Horários disponíveis encontrados: " + ", ".join(horarios_encontrados) + ". Qual prefere?"
            dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(text=f"Desculpe, não há horários disponíveis para {especialidade} em {data_preferida} às {hora_preferida}. Gostaria de tentar outra data/hora?")

        return [SlotSet("horarios_disponiveis", horarios_encontrados), SlotSet("status_disponibilidade", status)]


class ActionAgendarConsulta(Action):
    def name(self) -> Text:
        return "action_agendar_consulta"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        especialidade = tracker.get_slot("especialidade")
        data_hora_confirmada = tracker.get_slot("data_preferida")
        hora_confirmada = tracker.get_slot("hora_preferida")
        nome_paciente = tracker.get_slot("nome_paciente")

        print(f"Agendando consulta para {nome_paciente}: {especialidade} em {data_hora_confirmada} as {hora_confirmada}")
        
        id_agendamento_gerado = "AG" + "".join(random.choice(string.digits) for _ in range(6))
        status_agendamento = "sucesso"

        if status_agendamento == "sucesso":
            pass
        else:
            dispatcher.utter_message(text="Houve um problema ao realizar o seu agendamento. Por favor, tente novamente.")

        return [SlotSet("id_agendamento", id_agendamento_gerado), SlotSet("status_agendamento", status_agendamento)]