import decimal
import json
from datetime import datetime, timedelta
from http import HTTPStatus

from django.db.models import Max, Sum, F
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import render, redirect
# Create your views here.
from django.template import loader
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView

from apps.accounts.models import Account, Payments
from apps.accounts.views import create_payment
from apps.clients.models import Client
from apps.orders.models import Order, OrderDetail
from apps.products.models import Product, ProductStore
from apps.products.views import store_output, store_input
from apps.rooms.models import RoomGroup, RoomType, Room, RoomState
from apps.users.models import User
from house import settings
from django.utils import timezone


class ListOrder(ListView):
    model = Order
    template_name = 'orders/order.html'
    context_object_name = 'order_set'

    def get_queryset(self):
        return RoomGroup.objects.filter(is_state=True)  # Consulta para obtener todos los productos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_set'] = RoomType.objects.filter(is_state=True)
        context['group_set'] = self.get_queryset()

        return context


def modal_orders(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        if pk:
            try:
                my_date = datetime.now()
                room_obj = Room.objects.get(id=int(pk))
                t = loader.get_template('orders/order_modal.html')
                c = ({
                    'room_obj': room_obj,
                    'order': room_obj.get_order(),
                    'date_now': my_date.strftime("%Y-%m-%dT%H:%M")
                })
                return JsonResponse({
                    'success': True,
                    'form': t.render(c, request),
                }, status=HTTPStatus.OK)
            except Room.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'No existe la habitacion',
                }, status=HTTPStatus.OK)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e),
                }, status=HTTPStatus.OK)


@csrf_exempt
def create_order(request):
    if request.method == 'POST':
        order_json = request.POST.get('order', '')
        order = json.loads(order_json)
        room_status = order['status']
        client = order['client']
        if int(client) > 0:
            client_obj = Client.objects.get(id=int(client))
        else:
            client_obj = None
        current_time = order['current']
        if current_time:
            # init = timezone.make_aware(datetime.strptime(init, '%Y-%m-%dT%H:%M'), timezone.get_current_timezone())
            current_time = datetime.strptime(current_time, '%Y/%m/%d %I:%M %p')
            current = current_time.date()
        else:
            current_time = None
            current = None
        room = order['room']
        room_obj = None
        if int(room) > 0:
            room_obj = Room.objects.get(id=int(room))
        else:
            room_obj = None
        user = request.user.id
        user_obj = User.objects.get(id=user)
        subsidiary_obj = user_obj.subsidiary
        order_status = 'P'
        pk = order['order']
        order_obj = None
        if int(pk) > 0:
            if room_status == 'D':
                order_status = 'C'
            elif room_status == 'M':
                order_status = 'C'
            else:
                order_status = 'P'
            pk = int(pk)
            order_obj = Order.objects.get(id=pk)
            order_obj.user = user_obj
            order_obj.client = client_obj
            order_obj.subsidiary = subsidiary_obj
            order_obj.status = order_status
            order_obj.save()
        else:
            order_obj = Order.objects.create(
                type='S',
                number=get_correlative(subsidiary=subsidiary_obj, types='S'),
                current=current,
                date_time=current_time,
                user=user_obj,
                subsidiary=subsidiary_obj,
                client=client_obj,
                status=order_status,
                room=room_obj
            )
        if order_obj:
            for d in order['Detail']:
                detail = d['detail']
                product = d['product']
                product_obj = None
                types = 'P'
                description = d['description']
                quantity = d['quantity']
                if float(quantity) > 0:
                    quantity = decimal.Decimal(quantity)
                else:
                    quantity = decimal.Decimal(0.00)
                price = d['price']
                if float(price) > 0:
                    price = decimal.Decimal(price)
                else:
                    price = decimal.Decimal(0.00)
                store = d['store']
                store_obj = None
                if int(store) > 0:
                    store_obj = ProductStore.objects.get(id=int(store))
                else:
                    store_obj = None
                detail_obj = None
                if int(detail) > 0:
                    dk = int(detail)
                    detail_obj = OrderDetail.objects.get(id=dk)
                    detail_obj.quantity = quantity
                    detail_obj.price = price
                    detail_obj.save()
                else:
                    if product.isdigit():
                        product_obj = Product.objects.get(id=int(product))
                        types = 'P'
                    else:
                        product_obj = None
                        types = product
                    date_time = d['date']
                    date_time = datetime.strptime(date_time, '%Y/%m/%d %I:%M %p')
                    time = d['time']
                    times = datetime.strptime(time, '%H:%M')
                    times_timedelta = timedelta(hours=times.hour, minutes=times.minute)
                    detail_obj = OrderDetail.objects.create(
                        order=order_obj,
                        type=types,
                        room=room_obj,
                        product=product_obj,
                        description=description,
                        quantity=quantity,
                        old_quantity=quantity,
                        price=price,
                        init=date_time if types in ('H', 'R') else None,
                        end=date_time + times_timedelta if types in ('H', 'R') else None,
                        time=times if types in ('H', 'R') else None,
                        store=store_obj
                    )
                    if detail_obj:
                        if detail_obj.product:
                            store_output(detail=detail_obj)

            for py in order['Payment']:
                payment = py['payment']
                if int(payment) > 0:
                    payment = int(payment)
                else:
                    payment = None
                account = py['account']
                account_obj = None
                if int(account) > 0:
                    account_obj = Account.objects.get(id=int(account))
                else:
                    account_obj = None
                code = py['code']
                amount = py['amount']
                if float(amount) > 0:
                    amount = decimal.Decimal(amount)
                else:
                    amount = decimal.Decimal(0.00)
                create_payment(order=order_obj, pk=payment, account=account_obj, code=code, user=user_obj,
                               amount=amount)
            room_state_obj = RoomState.objects.filter(type=room_status).first()
            room_obj.state = room_state_obj
            room_obj.save()
            return JsonResponse({
                'success': True,
                'order': order_obj.id,
                'status': order_obj.room.status,
                'message': 'Operacion exitosa'
            }, status=HTTPStatus.OK)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Ocurrio un problema en el proceso'
            }, status=HTTPStatus.OK)
    else:
        return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def order_room(request, pk):
    if request.method == 'GET':
        my_date = datetime.now()
        print("Fecha:", my_date)
        user = request.user.id
        user_obj = User.objects.get(id=int(user))
        subsidiary_obj = user_obj.subsidiary
        room_obj = Room.objects.get(id=int(pk))
        product_set = Product.objects.filter(is_state=True)
        account_set = Account.objects.filter(is_state=True, subsidiary=subsidiary_obj)
        return render(request, 'orders/order_room.html', {
            'product_set': product_set,
            'room_obj': room_obj,
            'account_set': account_set,
            'order': room_obj.get_order(),
            'state_set': RoomState._meta.get_field('type').choices,
            'date_now': my_date.strftime("%Y-%m-%dT%H:%M")
        })


def get_correlative(subsidiary=None, types=None):
    if subsidiary is not None:
        number = Order.objects.filter(type=types, subsidiary=subsidiary).aggregate(
            r=Coalesce(Max('number'), int(0))).get('r')
        return number + 1


class OrdersList(ListView):
    model = Account
    template_name = 'orders/orders.html'
    context_object_name = 'order_set'

    def get_context_data(self, **kwargs):
        my_date = datetime.now().date()
        order_set = Order.objects.filter(current__range=(my_date, my_date), type='A')
        context = {
            'order_set': order_set,
            'type_set': Order._meta.get_field('type').choices,
            'date': my_date.strftime("%Y-%m-%d")
        }
        return context


def get_orders(request):
    if request.method == 'GET':
        init = request.GET.get('init', '')
        end = request.GET.get('end', '')
        types = request.GET.get('type', '')
        if types and init and end:
            try:
                order_set = Order.objects.filter(current__range=(init, end), type=types)
                t = loader.get_template('orders/orders_grid.html')
                c = ({
                    'order_set': order_set
                })
                return JsonResponse({
                    'success': True,
                    'grid': t.render(c, request),
                })
            except Order.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'No existe ninguna orden',
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e),
                })


def get_orders_month(request):
    if request.method == 'GET':
        date_ = datetime.now()
        year = date_.year
        month = date_.month
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = user_obj.subsidiary
        sales = []
        purchase = []
        m = 1
        while m <= 12:
            s = OrderDetail.objects.filter(order__type='S',
                                           order__create_at__year=year, order__create_at__month=m,
                                           order__status='C', order__subsidiary=subsidiary_obj).aggregate(
                r=Coalesce(Sum(F('quantity') * F('price')), decimal.Decimal(0))).get('r')
            e = OrderDetail.objects.filter(order__type='E',
                                           order__create_at__year=year, order__create_at__month=m,
                                           order__status='C', order__subsidiary=subsidiary_obj).aggregate(
                r=Coalesce(Sum(F('quantity') * F('price')), decimal.Decimal(0))).get('r')
            sales.append(s)
            purchase.append(e)
            m += 1
        return JsonResponse({
            'sales': sales,
            'purchase': purchase,
        }, status=HTTPStatus.OK)


def get_room_week(request):
    if request.method == 'GET':
        date_ = datetime.now()
        week = date_.weekday()
        init = date_ - timedelta(days=int(week))
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = user_obj.subsidiary
        output = []
        days = []
        for i in range(1, 8, 1):
            y = init.year
            m = init.month
            d = init.day
            order_set = OrderDetail.objects.filter(order__type='S', order__subsidiary=subsidiary_obj, order__status='C',
                                                   order__create_at__year=y, order__create_at__month=m,
                                                   order__create_at__day=d)
            room = order_set.aggregate(
                r=Coalesce(Sum(F('quantity') * F('price')), decimal.Decimal(0.00))).get('r')
            output.append(room)
            days.append(d)
            init = init + timedelta(days=1)
        return JsonResponse({
            'output': output,
            'days': days
        }, status=HTTPStatus.OK)


class ListPurchase(ListView):
    model = Order
    template_name = 'orders/purchase.html'
    context_object_name = 'order_set'
    my_date = datetime.now()

    def get_queryset(self):
        return Order.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group_set'] = self.get_queryset()
        context['type_set'] = self.model._meta.get_field('type').choices
        context['date_now'] = self.my_date.strftime("%Y-%m-%d")
        context['account_set'] = Account.objects.all()

        return context


@csrf_exempt
def create_purchase(request):
    if request.method == 'POST':
        order_json = request.POST.get('order', '')
        order = json.loads(order_json)
        client = order['client']
        if int(client) > 0:
            client_obj = Client.objects.get(id=int(client))
        else:
            client_obj = None
        date = order['date']
        user = request.user.id
        user_obj = User.objects.get(id=user)
        subsidiary_obj = user_obj.subsidiary
        types = order['type']
        pk = order['order']
        if int(pk) > 0:
            pk = int(pk)
        else:
            pk = None
        obj, created = Order.objects.update_or_create(
            id=pk,
            defaults={
                "type": types,
                "number": get_correlative(subsidiary=subsidiary_obj, types=types),
                "current": date,
                "date_time": datetime.now(),
                "user": user_obj,
                "client": client_obj,
                "subsidiary": subsidiary_obj,
                "status": 'C'
            })
        if obj:
            for d in order['Detail']:
                detail = d['detail']
                product = d['product']
                product_obj = None
                if int(product) > 0:
                    product_obj = Product.objects.get(id=int(product))
                else:
                    product_obj = None
                description = d['description']
                quantity = d['quantity']
                if float(quantity) > 0:
                    quantity = decimal.Decimal(quantity)
                else:
                    quantity = decimal.Decimal(0.00)
                price = d['price']
                if float(price) > 0:
                    price = decimal.Decimal(price)
                else:
                    price = decimal.Decimal(0.00)
                store = d['store']
                store_obj = None
                if int(store) > 0:
                    store_obj = ProductStore.objects.get(id=int(store))
                else:
                    store_obj = None
                dk = None
                if int(detail) > 0:
                    dk = int(detail)
                else:
                    dk = None
                detail_obj, detail_created = OrderDetail.objects.update_or_create(
                    id=dk,
                    defaults={
                        "order": obj,
                        "product": product_obj,
                        "description": description,
                        "quantity": quantity,
                        "old_quantity": quantity,
                        "price": price,
                        "store": store_obj
                    })
                if detail_obj:
                    if detail_created and detail_obj.product:
                        store_input(detail=detail_obj)
            for p in order['Payment']:
                payment = p['payment']
                if int(payment) > 0:
                    payment = int(payment)
                else:
                    payment = None
                account = p['account']
                account_obj = None
                if int(account) > 0:
                    account_obj = Account.objects.get(id=int(account))
                else:
                    account_obj = None
                code = p['code']
                amount = p['amount']
                if float(amount) > 0:
                    amount = decimal.Decimal(amount)
                else:
                    amount = decimal.Decimal(0.00)
                create_payment(order=obj, pk=payment, account=account_obj, code=code, user=user_obj, amount=amount)
            return JsonResponse({
                'success': True,
                'order': obj.id,
                'message': 'Operacion exitosa'
            }, status=HTTPStatus.OK)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Ocurrio un problema en el proceso'
            }, status=HTTPStatus.OK)
    else:
        return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def cancel_order(request):
    if request.method == 'GET':
        order = request.GET.get('order', '')
        if int(order) > 0:
            order_obj = Order.objects.get(id=int(order))
            order_obj.status = 'A'
            order_obj.save()
            for d in OrderDetail.objects.filter(order=order_obj):
                if d.product:
                    store_input(detail=d)
            payment_set = Payments.objects.filter(order=order_obj)
            for payment in payment_set:
                payment.status = 'A'
                payment.save()
            return JsonResponse({
                'success': True,
                'message': 'Orden anulada correctamente'
            }, status=HTTPStatus.OK)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Ocurrio un problema en el proceso'
            }, status=HTTPStatus.OK)
