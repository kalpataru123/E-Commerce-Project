from carts.models import Cart, CartItem
from carts.views import _cart_id

def counter(request):

    if 'admin' in request.path:
        return {}

    cart_count = 0

    try:
        if request.user.is_authenticated:
            # ✅ Logged in user cart
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            # ✅ Guest cart
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for item in cart_items:
            cart_count += item.quantity

    except:
        cart_count = 0

    return dict(cart_count=cart_count)
