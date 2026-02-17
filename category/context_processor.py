from .models import Category
def menu_links(request):
    categories = Category.objects.all()
    return {'links': categories}
