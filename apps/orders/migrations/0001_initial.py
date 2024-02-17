# Generated by Django 4.2.6 on 2024-02-15 15:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('subsidiaries', '0001_initial'),
        ('rooms', '0001_initial'),
        ('providers', '0001_initial'),
        ('clients', '0001_initial'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('E', 'ENTRADA'), ('S', 'SALIDA')], default='V', max_length=1, verbose_name='TIPO')),
                ('number', models.IntegerField(blank=True, null=True, verbose_name='CORRELATIVO')),
                ('status', models.CharField(choices=[('P', 'PENDIENTE'), ('C', 'COMPLETADO'), ('A', 'ANULADO')], default='P', max_length=1, verbose_name='ESTADO')),
                ('init', models.DateTimeField(blank=True, null=True)),
                ('end', models.DateTimeField(blank=True, null=True)),
                ('current', models.DateField(blank=True, null=True)),
                ('create_at', models.DateTimeField(auto_now_add=True)),
                ('update_at', models.DateTimeField(auto_now=True)),
                ('relative', models.IntegerField(default=0, verbose_name='ORDER RELACIONAL')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='clients.client', verbose_name='CLIENTE')),
                ('provider', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='providers.provider', verbose_name='PROVEEDOR')),
                ('subsidiary', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='subsidiaries.subsidiary')),
            ],
            options={
                'verbose_name': 'Orden',
                'verbose_name_plural': 'Ordenes',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='OrderDetail',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('H', 'HABITACION'), ('R', 'REINTEGRO'), ('P', 'PRODUCTO'), ('A', 'PERSONA ADICIONAL')], default='P', max_length=1, verbose_name='TIPO')),
                ('description', models.TextField(blank=True, default=None, max_length=150, null=True)),
                ('quantity', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Cantidad')),
                ('old_quantity', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Cantidad Anterior')),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Precio')),
                ('create_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('update_at', models.DateTimeField(auto_now=True, null=True)),
                ('init', models.DateTimeField(blank=True, null=True)),
                ('end', models.DateTimeField(blank=True, null=True)),
                ('refund', models.DateTimeField(blank=True, null=True)),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='orders.order')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.product')),
                ('room', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='rooms.room')),
                ('store', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.productstore', verbose_name='Almacen Producto')),
            ],
            options={
                'verbose_name': 'Orden Detalle',
                'verbose_name_plural': 'Ordene Detalles',
                'ordering': ['id'],
            },
        ),
    ]
