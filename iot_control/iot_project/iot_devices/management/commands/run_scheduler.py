import time
import threading
import paho.mqtt.publish as publish_helper

from django.core.management.base import BaseCommand
from django.utils import timezone
from iot_devices.models import AgendamentoIrrigacao

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

def executar_acionamento(topico, duracao, agendamento_id):
    """Executa a irrigação em uma thread separada sem travar o loop de checagem."""
    try:
        topico_limpo = topico.strip()
        print(f"[WORKER] #{agendamento_id} Iniciando rega: ligando '{topico_limpo}' por {duracao}s...")
        publish_helper.single(topico_limpo, payload="on", hostname=MQTT_BROKER, port=MQTT_PORT, qos=1)
        
        time.sleep(duracao)
        
        publish_helper.single(topico_limpo, payload="off", hostname=MQTT_BROKER, port=MQTT_PORT, qos=1)
        print(f"[WORKER] #{agendamento_id} Rega finalizada: '{topico_limpo}' desligado.")
        
    except Exception as e:
        print(f"[WORKER] #{agendamento_id} Erro ao enviar comando MQTT: {e}")


class Command(BaseCommand):
    help = "Worker de checagem e execução de agendamentos de irrigação"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("[WORKER] Worker de agendamento iniciado! Pressione CTRL+C para parar."))

        while True:
            try:
                agora = timezone.now()
                agendamentos_pendentes = AgendamentoIrrigacao.objects.filter(
                    executado=False,
                    data_hora__lte=agora
                )

                for agendamento in agendamentos_pendentes:
                    agendamento.executado = True
                    agendamento.save()

                    thread = threading.Thread(
                        target=executar_acionamento,
                        args=(agendamento.device.topic, agendamento.duracao_segundos, agendamento.id),
                        daemon=False
                    )
                    thread.start()

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[WORKER] Erro no ciclo de checagem: {e}"))

            time.sleep(5)