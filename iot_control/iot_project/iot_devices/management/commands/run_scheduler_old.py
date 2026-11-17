import time
import threading
from datetime import datetime
import paho.mqtt.publish as publish_helper

from django.core.management.base import BaseCommand
from django.utils import timezone
from iot_devices.models import AgendamentoIrrigacao

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

def executar_acionamento(topico, duracao, agendamento_id):
    """Executa a irrigação em uma thread separada sem travar o loop de checagem."""
    try:
        print(f"[WORKER] Iniciando rega: ligando {topico} por {duracao}s...")
        publish_helper.single(topico, payload="on", hostname=MQTT_BROKER, port=MQTT_PORT)
        
        time.sleep(duracao)
        
        publish_helper.single(topico, payload="off", hostname=MQTT_BROKER, port=MQTT_PORT)
        print(f"[WORKER] Rega finalizada: {topico} desligado.")
        
    except Exception as e:
        print(f"[WORKER] Erro ao enviar comando MQTT: {e}")


class Command(BaseCommand):
    help = "Worker de checagem e execução de agendamentos de irrigação"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("[WORKER] Worker de agendamento iniciado! Pressione CTRL+C para parar."))

        while True:
            try:
                agora = timezone.now()
                # Busca tarefas pendentes cuja data/hora já chegou ou passou
                agendamentos_pendentes = AgendamentoIrrigacao.objects.filter(
                    executado=False,
                    data_hora__lte=agora
                )

                for agendamento in agendamentos_pendentes:
                    # Marca como executado imediatamente para evitar disparos duplicados
                    agendamento.executado = True
                    agendamento.save()

                    topico_atuador = agendamento.device.topic
                    tempo_duracao = agendamento.duracao_segundos

                    # Dispara a rega em uma thread independente
                    thread = threading.Thread(
                        target=executar_acionamento,
                        args=(topico_atuador, tempo_duracao, agendamento.id)
                    )
                    thread.daemon = True
                    thread.start()

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[WORKER] Erro no ciclo de checagem: {e}"))

           
            time.sleep(5)