from django.db import models
from django.contrib.auth.models import User

#aqui são os dispositivos atuadores (a valvula)
class CommandDevice(models.Model): 
    name = models.CharField(max_length=100)
    topic = models.CharField(max_length=200, unique=True)
    status_topic = models.CharField(max_length=200, unique=True, null=True, blank=True)
    status = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {'LIGADO' if self.status else 'DESLIGADO'}"  
    

# aqui dispositivos de leitura (os sensores)
class SensorDevice(models.Model):
    TIPO_SENSOR = [ #adicionamos escolha de tipos de sensor
        ('Temperatura', 'Temperatura'),        
        ('Humidade', 'Humidade'),
    ]

    name = models.CharField(max_length=100)
    topic = models.CharField(max_length=200, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)    
    current_value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=10, editable=False)
    tipo_sensor = models.CharField(max_length=15, choices=TIPO_SENSOR, default="Temperatura")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.current_value if self.current_value is not None else 'N/D'} {self.unit})"

    def save(self, *args, **kwargs): #unidades por tipo
        if self.tipo_sensor == 'Temperatura':
            self.unit = '°C'
        elif self.tipo_sensor == 'Humidade':
             self.unit = '%'    
        super().save(*args, **kwargs)  

# Configurações de Irrigação = quando ligar 
class IrrigationConfig(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Sensores e atuador selecionados
    temp_sensor = models.ForeignKey(
        SensorDevice, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name="config_temp"
    )
    hum_sensor = models.ForeignKey(
        SensorDevice, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name="config_hum"
    )
    actuator = models.ForeignKey(
        CommandDevice, 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )

    temp_limit = models.FloatField(default=30.0)
    hum_limit = models.FloatField(default=40.0)
    auto_mode = models.BooleanField(default=False)
    valve_is_on = models.BooleanField(default=False)

    def __str__(self):
        return f"Config Irrigação - User: {self.user.username}"


class AgendamentoIrrigacao(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device = models.ForeignKey(CommandDevice, on_delete=models.CASCADE, help_text="Válvula ou atuador")
    data_hora = models.DateTimeField(help_text="Data e hora para iniciar a irrigação")
    duracao_segundos = models.PositiveIntegerField(default=10, help_text="Duração da rega em segundos")
    executado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_hora']

    def __str__(self):
        status = "Executado" if self.executado else "Pendente"
        return f"{self.device.name} - {self.data_hora.strftime('%d/%m/%Y %H:%M')} ({status})"