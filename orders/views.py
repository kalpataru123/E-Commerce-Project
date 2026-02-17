from django.http import JsonResponse,HttpResponse
from django.shortcuts import render, redirect,get_object_or_404
from carts.models import CartItem
from orders.forms import OrderForm
from .models import Order, Payment, OrderProduct
import datetime
import json
from django.core.mail import send_mail
from django.conf import settings
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors



def payment(request):

    if request.method != "POST":
        return JsonResponse({'error':'Invalid request'})

    body = json.loads(request.body)

    try:
        order = Order.objects.get(order_number=body['order_number'])
    except Order.DoesNotExist:
        return JsonResponse({'error':'Order not found'})

    payment = Payment.objects.create(
        user=request.user,
        payment_id=body['transaction_id'],
        payment_method=body['payment_method'],
        amount_paid=body['amount_paid'],
        status=body['status']
    )

    order.payment = payment
    order.is_ordered = True
    order.status = 'Completed'
    order.save()

    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        OrderProduct.objects.create(
            order=order,
            payment=payment,
            user=request.user,
            product=item.product,
            quantity=item.quantity,
            product_price=item.product.price,
            ordered=True
        )

    cart_items.delete()

    send_mail(
        'Order Success',
        f'Your order {order.order_number} has been placed successfully.',
        settings.EMAIL_HOST_USER,
        [order.email],
        fail_silently=False,
    )

    return JsonResponse({
    'redirect_url': f'/orders/payment_done/?order_number={order.order_number}&payment_id={payment.payment_id}'
    })


def place_order(request, total=0, quantity=0):

    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0

    # ✅ Correct total calculation
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax

    # ✅ Form Submit
    if request.method == 'POST':

        form = OrderForm(request.POST)

        if form.is_valid():

            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')

            data.save()

            # ✅ Order Number Generate
            current_date = datetime.date.today().strftime("%Y%m%d")
            order_number = current_date + str(data.id)

            data.order_number = order_number
            data.save()

            # ✅ Context
            context = {
                'order': data,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'usd_total': round(grand_total / 83, 2)
            }


            return render(request, 'orders/payment.html', context)

    return redirect('checkout')


def payment_done(request):

    order_number = request.GET.get('order_number')
    payment_id = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        payment = Payment.objects.get(payment_id=payment_id)

        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for item in ordered_products:
            subtotal += item.product_price * item.quantity

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'payment_id': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }

        return render(request, 'orders/payment_done.html', context)

    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
    
def download_invoice(request, order_number, payment_id):

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        payment = Payment.objects.get(payment_id=payment_id)
        ordered_products = OrderProduct.objects.filter(order=order)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice_{order_number}.pdf"'

        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Invoice", styles['Title']))
        elements.append(Paragraph(f"Order Number: {order.order_number}", styles['Normal']))
        elements.append(Paragraph(f"Payment ID: {payment.payment_id}", styles['Normal']))
        elements.append(Paragraph(" ", styles['Normal']))

        # Table data
        data = [['Product', 'Quantity', 'Price']]

        subtotal = 0

        for item in ordered_products:
            data.append([
                item.product.product_name,
                item.quantity,
                f"₹ {item.product_price}"
            ])
            subtotal += item.product_price * item.quantity

        data.append(['', '', ''])
        data.append(['Subtotal', '', f"₹ {subtotal}"])
        data.append(['Tax', '', f"₹ {order.tax}"])
        data.append(['Grand Total', '', f"₹ {order.order_total}"])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(table)

        doc.build(elements)

        return response

    except:
        return HttpResponse("Invoice not found")

   
