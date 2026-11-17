import threading
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import requests

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "topicIrrigacao_ifsc/#"
API_URL = "http://localhost:8000/iot/update_sensor_by_topic/"

def _enviar_para_django(topic, value):
    try:
        requests.post(
            API_URL,
            data={"topic": topic, "value": value},
            timeout=3
        )
    except Exception as e:
        print("Erro ao atualizar Django via API:", e)

def on_connect(client, userdata, flags, rc):
    print("Conectado ao broker com código:", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    topic_recebido = msg.topic.strip()
    payload_str = msg.payload.decode().strip()

    try:
        payload_value = float(payload_str)
        # Envia em thread separada para nunca travar o envio de comandos MQTT
        threading.Thread(
            target=_enviar_para_django,
            args=(topic_recebido, payload_value),
            daemon=True
        ).start()
    except ValueError:
        pass

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=60)
mqtt_client.loop_start()

def publish_message(topic, message):
    topic_limpo = topic.strip()

    if mqtt_client.is_connected():
        info = mqtt_client.publish(topic_limpo, message, qos=1)
        info.wait_for_publish()
        print(f"Comando '{message}' publicado em '{topic_limpo}' (conexão ativa)")
    else:
        # Fallback: abre conexão dedicada, aguarda confirmação de envio e fecha corretamente
        publish.single(
            topic_limpo,
            payload=message,
            hostname=MQTT_BROKER,
            port=MQTT_PORT,
            qos=1
        )
        print(f"Comando '{message}' publicado em '{topic_limpo}' (conexão avulsa)")