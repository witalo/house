$(function () {
    //Enable check and uncheck all functionality
    $('.checkbox-toggle').click(function () {
        var clicks = $(this).data('clicks')
        if (clicks) {
            //Uncheck all checkboxes
            $('.mailbox-messages input[type=\'checkbox\']').prop('checked', false)
            $('.checkbox-toggle .far.fa-check-square').removeClass('fa-check-square').addClass('fa-square')
        } else {
            //Check all checkboxes
            $('.mailbox-messages input[type=\'checkbox\']').prop('checked', true)
            $('.checkbox-toggle .far.fa-square').removeClass('fa-square').addClass('fa-check-square')
        }
        $(this).data('clicks', !clicks)
    })
})
$(document).ready(function () {
    new Autocomplete('#autocomplete-product', {
        search: input => {
            const url = `/products/search_product/?search=${encodeURI(input.toUpperCase())}`

            return new Promise(resolve => {
                if (input.length < 3) {
                    $('#search-code').val('')
                    return resolve([])
                }
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        resolve(data.product)
                    })
            })
        },
        renderResult: (result, props) => {
            let group = ''
            if (result.index % 3 === 0) {
                group = '<li class="group">Digite</li>'
            }
            return `
                ${group}
                <li ${props} class="font-weight-bold small">
                 <div class="text-white h5">
                    ${'<i class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></i>'} ${result.name}
                 </div>
                 <div class="text-white-50 h6">
                    <b class="text-white">CODIGO: ${result.code}</b> <br>
                    MARCA : ${result.brand} <br>
                    PRECIO : ${result.price} <br>
                    STOCK : ${result.stock.quantity}
                  </div>
                </li>
                `
        },
        getResultValue: result => result.name,
        onSubmit: result => {
            if (result) {
                AddRowDetail(0, 0, result.pk, result.code, result.name, 1, result.price, result.stock.id, result.stock.quantity)
            }
        }
    })
})

async function AddRowDetail(i, pk, product, code, name, q, p, s, k) {
    let quantity = parseFloat(q).toFixed(0)
    let stock = parseFloat(k).toFixed(0)
    if (stock < quantity) {
        toastr.warning('Stock insuficiente Total=' + stock.toString())
        return false
    }
    let price = parseFloat(p).toFixed(2)
    let amount = parseFloat(q * p).toFixed(2)
    $('tbody#order_detail').append(
        '<tr class="p-0"  pk="' + pk + '" i="' + i + '" store="' + s + '" product="' + product + '">' +
        '<td class="align-middle item-number p-1 text-center">' +
        '<div class="icheck-primary">' +
        '<input class="input-number" type="checkbox" value="" id="' + i + '">' +
        '<label for="' + i + '">' + '</label>' +
        '</div>' +
        '</td>' +
        '<td class="mailbox-star align-middle item-quantity">' +
        '<div class="input-group input-group-sm">' +
        '<div class="input-group-prepend">' +
        '<div class="btn btn-primary btn-prev">' +
        '<i class="fa fa-minus-circle"></i>' +
        '</div>' +
        '</div>' +
        '<input type="number" min="0" step="1" value="' + quantity + '" class="form-control text-center input-quantity" placeholder="0">' +
        '<div class="input-group-append">' +
        '<div class="btn btn-primary btn-next">' +
        '<i class="fa fa-plus-circle"></i>' +
        '</div>' +
        '</div>' +
        '</div>' +
        '</td>' +
        '<td class="mailbox-subject align-middle item-name" description="' + name + '">' +name + '</td>' +
        '<td class="mailbox-attachment align-middle item-price">' + '<input type="number" step="0.01" min="0.00" placeholder="0.00" class="form-control form-control-sm input-price text-right w-100" value="' + price + '" style="width: 85px;"/>' + '</td>' +
        '<td class="align-middle mailbox-date item-amount p-1 text-right">' + amount + '</td>' +
        '<td class="align-middle p-1 text-center item-delete">' +
        '    <button type="button" class="btn btn-danger rounded">' + '<i class="fa fa-trash-alt">' + '</i>' + '</button>' +
        '</td>' +
        '</tr>'
    );
    CountRow()
    TotalDetail()
}

function CountRow() {
    let index = 1;
    $('tbody#order_detail tr').each(function () {
        let div = $(this).find('td.item-number div.icheck-primary')
        div.find('input.input-number').attr('id', index)
        div.find('label').attr('for', index)
        $(this).attr('i', index);
        let pk = $(this).attr('pk');
        let product = $(this).attr('product');
        $(this).find('td.item-delete button').attr('onclick', 'DeleteRowDetail(' + index + ', ' + pk + ', ' + product + ')')
        index++;
    });
};

function TotalDetail() {
    let total = 0;
    let total_room = $('#total_room').val()
    let total_refund = $("#total_refund").val()
    if (parseFloat(total_refund) > 0) {
        total_refund = parseFloat(total_refund).toFixed(2)
    } else {
        total_refund = parseFloat('0.00').toFixed(2)
    }
    if (total_room === '' || total_room === '0' || total_room === undefined || isNaN(total_room)) {
        total_room = parseFloat('0.00').toFixed(2)
    } else {
        total_room = parseFloat(total_room).toFixed(2)
    }
    $('tbody#order_detail tr td.item-amount').each(function () {
        if ($(this).text()) {
            total = total + parseFloat($(this).text());
        } else {
            total = total + parseFloat("0.00");
        }
    });
    let t = parseFloat(total) + parseFloat(total_room) + parseFloat(total_refund)
    $('#subtotal').val(total.toFixed(2))
    $('#total').val(t.toFixed(2))
};

function DeleteRowDetail(i, pk, product) {
    let rows = $('tbody#order_detail').find("tr[i=" + i + "][pk=" + pk + "][product=" + product + "]")
    if (parseInt(pk) > 0) {
        let order = $('#id-order').val()
        if (order != '' && parseInt(pk) > 0) {
            let r = confirm("¿Esta seguro de eliminar el detalle?")
            if (r == true) {
                $.ajax({
                    url: '/sales/delete_order_detail/',
                    async: true,
                    dataType: 'json',
                    type: 'GET',
                    data: {'pk': pk, 'o': 'I'},
                    success: function (response) {
                        if (response.success) {
                            rows.remove();
                            CountRow();
                            TotalDetail();
                            toastr.success(response.message)
                        } else {
                            toastr.error(response.message)
                        }
                    },
                });
            }
        } else {
            toastr.error('Necesita buscar una orden')
        }
    } else {
        rows.remove();
        CountRow();
        TotalDetail();
    }
}

function DeleteRowCheck() {
    $('tbody#order_detail tr').each(function () {
        if ($(this).find('td.item-number div.icheck-primary input.input-number').is(':checked')) {
            $(this).remove()
        }
    });
    CountRow();
    TotalDetail();
}

$(document).on('keyup change', 'tbody#order_detail tr td.item-quantity div.input-group input.input-quantity', function () {
    let input = $(this)
    let row = input.parent('div.input-group').parent('td.item-quantity').parent('tr')
    let td_amount = row.find('td.item-amount')
    let input_price = row.find('td.item-price input.input-price')
    let quantity = input.val()
    let price = input_price.val()
    if (parseFloat(quantity) > 0) {
        quantity = parseFloat(quantity).toFixed(2)
    } else {
        quantity = parseFloat('0.00').toFixed(2)
    }
    if (parseFloat(price) > 0) {
        price = parseFloat(price).toFixed(2)
    } else {
        price = parseFloat('0.00').toFixed(2)
    }
    let amount = parseFloat(quantity) * parseFloat(price)
    td_amount.text(amount.toFixed(2))
    TotalDetail()
})
$(document).on('keyup change', 'tbody#order_detail tr td.item-price input.input-price', function () {
    let input = $(this)
    let row = input.parent('td.item-price').parent('tr')
    let td_amount = row.find('td.item-amount')
    let input_quantity = row.find('td.item-quantity div.input-group input.input-quantity')
    let quantity = input_quantity.val()
    let price = input.val()
    if (parseFloat(quantity) > 0) {
        quantity = parseFloat(quantity).toFixed(2)
    } else {
        quantity = parseFloat('0.00').toFixed(2)
    }
    if (parseFloat(price) > 0) {
        price = parseFloat(price).toFixed(2)
    } else {
        price = parseFloat('0.00').toFixed(2)
    }
    let amount = parseFloat(quantity) * parseFloat(price)
    td_amount.text(amount.toFixed(2))
    TotalDetail()
})
$(document).on('click', 'tbody#order_detail tr td.item-quantity div.input-group div.input-group-prepend div.btn-prev', function () {
    let btn = $(this)
    let input_group = btn.parent('div.input-group-prepend').parent('div.input-group')
    let input = input_group.find('input.input-quantity')
    let quantity = input.val()
    if (parseInt(quantity) > 0) {
        quantity = parseInt(quantity) - 1
    } else {
        quantity = parseInt('0')
    }
    input.val(parseInt(quantity))
    input.trigger('change')
})
$(document).on('click', 'tbody#order_detail tr td.item-quantity div.input-group div.input-group-append div.btn-next', function () {
    let btn = $(this)
    let input_group = btn.parent('div.input-group-append').parent('div.input-group')
    let input = input_group.find('input.input-quantity')
    let quantity = input.val()
    if (parseInt(quantity) > 0) {
        quantity = parseInt(quantity)
    } else {
        quantity = parseInt('0')
    }
    quantity = quantity + 1
    input.val(parseInt(quantity))
    input.trigger('change')
})

function AddRowOther() {
    var product = prompt('DESCRIPCION DE LA COMPRA/ENTRADA?', '');
    if (product && product.trim() !== "") {
        // if ($("tbody#order_detail tr[product=" + 0 + " ]").length > 0) {
        //     toastr.info('El detalle ya se encuentra añadido')
        //     return false
        // } else {
        AddRowDetail(0, 0, 0, '-', product.toUpperCase(), 1, 0, 0, 1)
        // }
    }
}

function SearchProvider() {
    let document = $('#document').val();
    if (document.length === 8 || document.length === 11) {
        $('#id-loading').css('display', '')
        $.ajax({
            url: '/providers/get_provider/',
            dataType: 'json',
            type: 'GET',
            data: {'document': document},
            success: function (response) {
                if (response.pk) {
                    $("#client").val(response.pk);
                    $("#names").val(response.names);
                    $("#phone").val(response.phone);
                    $("#address").val(response.address);
                } else {
                    toastr.error(response.message)
                }
                $('#id-loading').css('display', 'none')
            },
            fail: function (response) {
                toastr.error('Ocurrio un problema en el proceso')
            }
        });
    } else {
        toastr.warning('Ingrese un dnumero de documento valido');
        return false;
    }
}

$('#document').keypress(function (e) {
    if (e.keyCode === 13) {
        e.preventDefault()
        $(this).trigger("enterKey");
        SearchProvider()
    }
});

function ClickProvider(h) {
    ClientSave($(h))
}

$('#names').keypress(function (e) {
    if (e.keyCode === 13) {
        e.preventDefault()
        $(this).trigger("enterKey");
        ClientSave($(this))
    }
});
$('#address').keypress(function (e) {
    if (e.keyCode === 13) {
        e.preventDefault()
        $(this).trigger("enterKey");
        ClientSave($(this))
    }
});
$('#phone').keypress(function (e) {
    if (e.keyCode === 13) {
        e.preventDefault()
        $(this).trigger("enterKey");
        ClientSave($(this))
    }
});

function ClientSave(n) {
    let pk = $('#client').val();
    if (pk !== '' && pk !== '0') {
        let address = $('#address').val();
        if ((n.val().length <= 5)) {
            toastr.warning('Ingrese 5 caractares almenos');
            return false;
        }
        let phone = $('#phone').val();
        let names = $('#names').val();
        $('#id-loading').css('display', '')
        $.ajax({
            url: '/providers/provider_save/',
            dataType: 'json',
            type: 'POST',
            data: {'pk': pk, 'names': names, 'address': address, 'phone': phone},
            success: function (response) {
                if (response.pk) {
                    toastr.success(response.message);
                    $("#client").val(response.pk);
                } else {
                    toastr.error(response.message)
                }
                $('#id-loading').css('display', 'none')
            },
            fail: function (response) {
                toastr.error('Ocurrio un problema en el proceso')
            }
        });
    }
}

function AddNewPayment() {
    // Obtiene la fecha y hora actual
    var fechaHoraActual = new Date();
    // Obtiene los componentes de la fecha y hora
    var dia = fechaHoraActual.getDate();
    var mes = fechaHoraActual.getMonth() + 1; // Los meses en JavaScript van de 0 a 11
    var año = fechaHoraActual.getFullYear();
    var horas = fechaHoraActual.getHours();
    var minutos = fechaHoraActual.getMinutes();
    var periodo = (horas >= 12) ? 'PM' : 'AM';
    // Formatea los componentes con ceros a la izquierda si es necesario
    dia = (dia < 10) ? '0' + dia : dia;
    mes = (mes < 10) ? '0' + mes : mes;
    horas = (horas % 12 || 12); // Convierte las horas a formato de 12 horas
    minutos = (minutos < 10) ? '0' + minutos : minutos;
    // Construye la cadena de fecha y hora en el formato deseado
    var fechaHoraFormateada = `${mes}/${dia}/${año} ${horas}:${minutos} ${periodo}`;

    let account = $('#account').val()
    let name = $('#account option:selected').text()
    let amount = $('#amount').val()
    let code = $('#code').val()
    if (parseFloat(amount) > 0 && parseInt(account) > 0) {
        let total = $('#total').val()
        if (parseFloat(total) >= 0) {
            total = parseFloat(total).toFixed(2)
        } else {
            total = parseFloat("0.00").toFixed(2)
        }
        let total_payment = $('#total-payment').val()
        if (parseFloat(total_payment) >= 0) {
            total_payment = parseFloat(total_payment).toFixed(2)
        } else {
            total_payment = parseFloat("0.00").toFixed(2)
        }
        if ((parseFloat(total_payment) + parseFloat(amount)) <= parseFloat(total)) {
            AddPayment(0, 0, account, name, amount, code, fechaHoraFormateada)
            $('#amount').val('')
            $('#account').val('0')
            $('#code').val('')
        } else {
            toastr.info('No puede realizar pagos que superen el monto total')
            return false
        }

    } else {
        toastr.info('Seleccione una cuenta e ingrese un monto valido')
        return false
    }
}

function AddPayment(i, pk, account, name, t, code, current) {
    let amount = parseFloat(t).toFixed(2)
    $('tbody#detail_payment').append(
        '<tr class="payment-row p-0"  pk="' + pk + '" i="' + i + '" a="' + account + '">' +
        '<td class="align-middle payment-number p-1 text-center">' + '<span class="bs-stepper-circle bg-gradient-lightblue">' + i + '</span>' +
        '</td>' +
        '<td class="align-middle payment-date p-1 text-center">' + current + '</td>' +
        '<td class="align-middle payment-account p-1">' + name + '</td>' +
        '<td class="align-middle payment-code p-1">' + code + '</td>' +
        '<td class="align-middle payment-amount p-1 text-right">' + amount + '</td>' +
        '<td class="align-middle payment-delete p-1 text-center">' +
        '    <button type="button" class="btn btn-sm btn-outline-danger rounded">' + '<i class="fa fa-trash-alt">' + '</i>' + '</button>' +
        '</td>' +
        '</tr>'
    );
    CountRowPayment();
    TotalDetailPayment();
}

function CountRowPayment() {
    let index = 1;
    $('tbody#detail_payment tr').each(function () {
        let tr = $(this)
        let span = tr.find('td.payment-number span.bs-stepper-circle')
        span.text(index)
        tr.attr('i', index);
        let pk = tr.attr('pk');
        let account = tr.attr('a');
        tr.find('td.payment-delete button').attr('onclick', 'DeleteRowPayment(' + index + ', ' + pk + ', ' + account + ')')
        index++;
    });
};

function TotalDetailPayment() {
    let total = parseFloat("0.00").toFixed(2);
    $('tbody#detail_payment tr.payment-row td.payment-amount').each(function () {
        let td = $(this)
        if (parseFloat(td.text()) > 0) {
            total = parseFloat(total) + parseFloat(td.text());
        } else {
            total = parseFloat(total) + parseFloat("0.00");
        }
    });
    $('#total-payment').val(parseFloat(total).toFixed(2))
};
$("select#account").on("keyup change", function (e) {
    let val = $(this).val();
    if (parseInt(val) > 0) {
        ValidateAccount(val).then(function (r) {
            // Hacer algo con los datos obtenidos
            if (r) {
                $(this).attr('pk', val)
                let total = $('#total').val()
                if (parseFloat(total) >= 0) {
                    total = parseFloat(total).toFixed(2)
                } else {
                    total = parseFloat("0.00").toFixed(2)
                }
                let total_payment = $('#total-payment').val()
                if (parseFloat(total_payment) >= 0) {
                    total_payment = parseFloat(total_payment).toFixed(2)
                } else {
                    total_payment = parseFloat("0.00").toFixed(2)
                }
                let amount = parseFloat(total) - parseFloat(total_payment)
                $('#amount').val(parseFloat(amount).toFixed(2))
            } else {
                $('#account').val("0")
                $('#amount').val('')
                $('#code').val('')
            }
        }).catch(function (error) {
            // Manejar errores
            console.error(error);
        });
    } else {
        $('#amount').val('')
        $('#code').val('')
    }

})

function DeleteRowPayment(i, pk, account) {
    let rows = $('tbody#detail_payment').find("tr[i=" + i + "][pk=" + pk + "][a=" + account + "]")
    if (parseInt(pk) > 0) {
        // let order = $('#id-order').val()
        // if (order != '' && parseInt(pk) > 0) {
        //     let r = confirm("¿Esta seguro de eliminar el detalle del pago?")
        // if (r == true) {
        //     $.ajax({
        //         url: '/sales/delete_order_detail/',
        //         async: true,
        //         dataType: 'json',
        //         type: 'GET',
        //         data: {'pk': pk, 'o': 'I'},
        //         success: function (response) {
        //             if (response.success) {
        //                 rows.remove();
        //                 CountRow();
        //                 TotalDetail();
        //                 toastr.success(response.message)
        //             } else {
        //                 toastr.error(response.message)
        //             }
        //         },
        //     });
        // }
        // } else {
        //     toastr.error('Necesita buscar una orden')
        // }
    } else {
        rows.remove();
        CountRowPayment();
        TotalDetailPayment();
    }
}

function CreateOrder() {
    let order = $('#order').val()
    if (parseInt(order) > 0) {
        order = parseInt(order)
    } else {
        order = 0
    }
    let client = $('#client').val()
    if (parseInt(client) > 0) {
        client = parseInt(client)
    } else {
        toastr.info('Es necesario el proveedor')
        return false
    }
    let date = $('#date').val()
    if (date === undefined) {
        toastr.info('Seleccione la fecha de la operacion')
        return false
    }
    let total = $('#total').val()
    if (parseFloat(total) > 0) {
        total = parseFloat(total).toFixed(2)
    } else {
        total = parseFloat('0.00').toFixed(2)
    }
    let type = $('#type').val()
    // var state = $("input[type='radio'][name='state']:checked").val();
    let Order = {
        "Detail": [],
        "Payment": [],
        "order": order,
        "type": type,
        "client": client,
        "date": date,
        "total": total
    };
    let val = true
    $("tbody#order_detail tr").each(function () {
        let row = $(this)
        let pk = row.attr('pk')
        let i = row.attr('i')
        let store = row.attr('store')
        if (store === '' || store === undefined) {
            toastr.info('Almacen desconocido en la fila ' + i.toString())
            val = false
            return val
        }
        let product = row.attr('product')
        if (product === '' || product === undefined) {
            toastr.info('Producto desconocido en la fila ' + i.toString())
            val = false
            return val
        }
        let description = row.find('td.item-name').attr('description')
        if (description === undefined || description === '') {
            toastr.info('Nombre de producto desconocido en la fila ' + i.toString())
            val = false
            return val
        }
        let quantity = row.find('td.item-quantity div.input-group input.input-quantity').val()
        if (parseFloat(quantity) === 0 || quantity === '' || quantity === undefined) {
            toastr.info('Ingrese una cantidad en la fila ' + i.toString())
            val = false
            return val
        }
        let price = row.find('td.item-price input.input-price').val()
        if (parseFloat(price) === 0 || price === '' || price === undefined) {
            toastr.info('Ingrese un precio en la fila ' + i.toString())
            val = false
            return val
        }
        let Detail = {
            "detail": pk,
            "product": parseInt(product),
            "description": description,
            "quantity": parseFloat(quantity).toFixed(2),
            "price": parseFloat(price).toFixed(2),
            "store": parseInt(store)
        };
        Order.Detail.push(Detail);
    })
    if (!val) {
        return false
    } else {
        let pay = true
        $("tbody#detail_payment tr").each(function () {
            let row = $(this)
            let pk = row.attr('pk')
            let i = row.attr('i')
            let a = row.attr('a')
            if (a === '' || a === undefined || a === '0' || parseInt(a) === 0) {
                toastr.info('Caja/Cuenta no encontrada en la fila ' + i.toString())
                pay = false
                return pay
            }
            let code = row.find('td.payment-code').text()
            let amount = row.find('td.payment-amount').text()
            if (parseFloat(amount) === 0 || amount === '' || amount === undefined) {
                toastr.info('Monto del pago invalido en la fila ' + i.toString())
                pay = false
                return pay
            }
            let Payment = {
                "payment": pk,
                "account": parseInt(a),
                "code": code,
                "amount": parseFloat(amount).toFixed(2)
            };
            Order.Payment.push(Payment);
        })
        if (!pay) {
            return false
        } else {
            SendOrder(Order)
        }
    }
}

function SendOrder(object) {
    let r = confirm('¿ESTA SEGURO DE PROCEDER CON LA ORDEN?');
    if (r === true) {
        $.ajax({
            url: '/orders/create_purchase/',
            dataType: 'json',
            type: 'POST',
            data: {'order': JSON.stringify(object)},
            success: function (response) {
                if (response.success) {
                    toastr.success(response.message)
                    setTimeout(function () {
                        location.reload();
                    }, 1000);
                } else {
                    toastr.error(response.message)
                }
            },
            error: function (jqXhr, textStatus, xhr) {
                if (jqXhr.status === 500) {
                    toastr.error(jqXhr.responseJSON.error);
                }
            }
        });
    }
}

function ValidateAccount(a) {
    return new Promise(function (resolve, reject) {
        // Realize la solicitud Ajax
        $.ajax({
            url: '/accounts/validate_account/',
            dataType: 'json',
            type: 'GET',
            data: {'pk': a},
            success: function (response) {
                if (response.success) {
                    toastr.success(response.message);
                    resolve(true);
                } else {
                    toastr.error(response.message)
                    resolve(false);
                }
            },
            fail: function (response) {
                toastr.error('Ocurrio un problema en el proceso')
                reject(false);
            }
        });
    });
}