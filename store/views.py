from django.shortcuts import render,get_object_or_404
from store.models import Product, Variation
from category.models import Category
from carts.views import _cart_id
from carts.models import CartItem
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q

# Create your views here.

def store(request, category_slug=None):
    if category_slug is not None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(is_available=True, category=categories)
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)

    product_count = products.count()
    context = {
        'products': paged_products,
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)

def product_detail(request, category_slug, product_slug):

    single_product = get_object_or_404(
        Product,
        category__slug=category_slug,
        slug=product_slug
    )

    # ⭐ Color Variations
    colors = Variation.objects.filter(
        product=single_product,
        variation_category__iexact='color',
        is_active=True
    )

    # ⭐ Size Variations
    sizes = Variation.objects.filter(
        product=single_product,
        variation_category__iexact='size',
        is_active=True
    )

    # ⭐ Check Cart
    in_cart = CartItem.objects.filter(
        cart__cart_id=_cart_id(request),
        product=single_product
    ).exists()

    context = {
        'single_product': single_product,
        'colors': colors,
        'sizes': sizes,
        'in_cart': in_cart,
    }

    return render(request, 'store/product-detail.html', context)

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_at').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
    context = {
        'products': products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)
