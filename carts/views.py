from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from carts.models import Cart, CartItem
from django.contrib.auth.decorators import login_required


# -------- Cart Session --------
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


# -------- Add Cart --------
def add_cart(request, product_id, cart_item_id=None):

    product = get_object_or_404(Product, id=product_id)

    # 🔥 Logged User Cart
    if request.user.is_authenticated:
        user = request.user
        cart_items = CartItem.objects.filter(product=product, user=user)

    # 🔥 Guest Cart
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))

        cart_items = CartItem.objects.filter(product=product, cart=cart)

    # Quantity Increase
    if cart_item_id:
        cart_item = get_object_or_404(CartItem, id=cart_item_id)
        cart_item.quantity += 1
        cart_item.save()
        return redirect('cart')

    product_variation = []

    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]

            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variation.append(variation)
            except:
                pass

    existing_variation_list = []
    id_list = []

    for item in cart_items:
        existing_variation_list.append(list(item.variations.all()))
        id_list.append(item.id)

    if product_variation in existing_variation_list:
        index = existing_variation_list.index(product_variation)
        item_id = id_list[index]
        cart_item = CartItem.objects.get(id=item_id)
        cart_item.quantity += 1
        cart_item.save()

    else:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=request.user
            )
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart
            )

        if product_variation:
            cart_item.variations.add(*product_variation)

        cart_item.save()

    return redirect('cart')


# -------- Remove Quantity --------
def remove_cart(request, product_id, cart_item_id):

    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item = get_object_or_404(
            CartItem,
            product=product,
            user=request.user,
            id=cart_item_id
        )
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = get_object_or_404(
            CartItem,
            product=product,
            cart=cart,
            id=cart_item_id
        )

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart')


# -------- Remove Full Item --------
def remove_cart_item(request, product_id, cart_item_id):

    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item = get_object_or_404(
            CartItem,
            product=product,
            user=request.user,
            id=cart_item_id
        )
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = get_object_or_404(
            CartItem,
            product=product,
            cart=cart,
            id=cart_item_id
        )

    cart_item.delete()
    return redirect('cart')


# -------- Cart Page --------
def cart(request, total=0, quantity=0, cart_items=None):

    tax = 0
    grand_total = 0

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax

    except:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }

    return render(request, 'store/cart.html', context)


# -------- Checkout --------
@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):

    tax = 0
    grand_total = 0

    cart_items = CartItem.objects.filter(user=request.user, is_active=True)

    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }

    return render(request, 'store/checkout.html', context)
