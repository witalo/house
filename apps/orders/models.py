from datetime import datetime, timedelta
import decimal
from django.db import models
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from apps.users.models import User
from django.utils import timezone
from django.utils.timezone import make_aware, localtime
import pytz

now = timezone.now()
desired_timezone = pytz.timezone('America/Lima')


# Create your models here.
class Order(models.Model):
    TYPE_CHOICES = (
        ('E', 'ENTRADA'),
        ('S', 'SALIDA')
    )
    STATUS_CHOICES = (('P', 'PENDIENTE'), ('C', 'COMPLETADO'), ('A', 'ANULADO'))
    id = models.AutoField(primary_key=True)
    type = models.CharField('TIPO', max_length=1, choices=TYPE_CHOICES, default='V')
    number = models.IntegerField(verbose_name='CORRELATIVO', null=True, blank=True)
    status = models.CharField('ESTADO', max_length=1, choices=STATUS_CHOICES, default='P')
    date_time = models.DateTimeField(null=True, blank=True)
    current = models.DateField(null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey('clients.Client', verbose_name='CLIENTE',
                               on_delete=models.SET_NULL, null=True, blank=True)
    provider = models.ForeignKey('providers.Provider', verbose_name='PROVEEDOR',
                                 on_delete=models.SET_NULL, null=True, blank=True)
    subsidiary = models.ForeignKey('subsidiaries.Subsidiary', on_delete=models.CASCADE, null=True, blank=True)
    relative = models.IntegerField(verbose_name='ORDER RELACIONAL', default=0)
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE, null=True, blank=True)

    def total(self):
        total = OrderDetail.objects.filter(order=self).aggregate(
            r=Coalesce(Sum(F('quantity') * F('price')), decimal.Decimal(0.00))).get('r')
        return round(total, 2)

    def get_expired(self):
        if self.status == 'P' and self.type == 'S' and self.room:
            detail_set = OrderDetail.objects.filter(type__in=['O', 'X'], order=self)
            if detail_set.exists():
                final_date = timezone.localtime(self.date_time, timezone=desired_timezone)
                # Obtener la fecha y hora actual con la zona horaria deseada
                date_time = datetime.now(desired_timezone)
                if detail_set.filter(type='X').exists():
                    refund_obj = detail_set.filter(type='X').first()
                    final_date = timezone.localtime(refund_obj.end, timezone=desired_timezone)
                elif detail_set.filter(room=self.room, type='O').exists():
                    room_obj = detail_set.filter(room=self.room, type='O').first()
                    final_date = timezone.localtime(room_obj.end, timezone=desired_timezone)
                else:
                    final_date = self.date_time
                return date_time >= final_date
            else:
                return False
        else:
            return False

    def get_time(self):
        if self.status == 'P' and self.type == 'S' and self.room:
            init_date = timezone.localtime(self.date_time, timezone=desired_timezone)
            date_time = datetime.now(desired_timezone)
            times = date_time - init_date
            days = times.days
            hours, seconds = divmod(times.seconds, 3600)
            minutes, _ = divmod(seconds, 60)
            return '{}:Diás {}:Horas {}:Minutos'.format(days, hours, minutes)
        else:
            return '{}:Diás {}:Horas {}:Minutos'.format(0, 0, 0)

    def save(self, *args, **kwargs):
        # Llamamos al método save() original para guardar el objeto Order
        super().save(*args, **kwargs)
        # Realizar la actualización del otro modelo relacionado aquí
        room_obj = self.room
        if room_obj:
            if self.status == 'C':
                from apps.rooms.models import RoomState
                room_state_set = RoomState.objects.filter(type='D')
                if room_state_set.exists():
                    room_state_obj = room_state_set.first()
                    room_obj.state = room_state_obj
                    room_obj.save()

    # def update(self, *args, **kwargs):
    #     # Llamamos al método update() original para actualizar el objeto Order
    #     super().update(*args, **kwargs)
    #
    #     # Realizar la actualización del otro modelo relacionado aquí
    #     room_obj = self.room
    #     if room_obj:
    #         if self.status == 'C':
    #             room_obj.state.type = 'D'
    #             room_obj.save()

    class Meta:
        verbose_name = 'Orden'
        verbose_name_plural = 'Ordenes'
        ordering = ['id']

    def __str__(self):
        return str(self.type) + "-" + str(self.number)


class OrderDetail(models.Model):
    TYPE_CHOICES = (
        ('O', 'HABITACION'),
        ('X', 'REINTEGRO'),
        ('P', 'PRODUCTO'),
        ('A', 'PERSONA ADICIONAL')
    )
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField('TIPO', max_length=1, choices=TYPE_CHOICES, default='P')
    description = models.TextField(max_length=150, blank=True, null=True, default=None)
    quantity = models.DecimalField('Cantidad', max_digits=10, decimal_places=2, default=0)
    old_quantity = models.DecimalField('Cantidad Anterior', max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2, default=0)
    store = models.ForeignKey(
        'products.ProductStore', verbose_name='Almacen Producto', on_delete=models.SET_NULL, null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    update_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    init = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    time = models.DurationField(null=True, blank=True)

    def amount(self):
        amount = round(decimal.Decimal(self.quantity * self.price), 2)
        return amount

    def get_time(self):
        hours = 0
        minutes = 0
        if self.time:
            total_minutes = self.time.total_seconds() // 60
            # Calcular las horas y minutos
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{int(hours):02d} HORA(S) Y {int(minutes):02d} MINUTO(S)"
        else:
            return f"{int(hours):02d} HORA(S) Y {int(minutes):02d} MINUTO(S)"

    class Meta:
        verbose_name = 'Orden Detalle'
        verbose_name_plural = 'Ordene Detalles'
        ordering = ['id']

    def __str__(self):
        name = "{} - {}".format(self.order.number, self.product.name)
        return str(name)
