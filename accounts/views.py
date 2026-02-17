from django.shortcuts import render, redirect,get_object_or_404
from .forms import RegistrationForm,UserForm,UserProfileForm
from .models import Account,UserProfile
from django.contrib import messages
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.urls import reverse
from carts.models import Cart, CartItem
from carts.views import _cart_id
from orders.models import Order,OrderProduct


# ----------------------
# LOGIN VIEW
# ----------------------

def login_page(request):

    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        user = auth.authenticate(request, username=email, password=password)

        if user is not None:

            if not user.is_active:
                messages.error(request, "Please activate your account via email.")
                return redirect('login')

            # ---------- MERGE CART BEFORE LOGIN ----------
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart)

                for item in cart_items:

                    product_variations = item.variations.all()

                    user_cart_items = CartItem.objects.filter(
                        user=user,
                        product=item.product
                    )

                    matched = False

                    for user_item in user_cart_items:

                        if set(user_item.variations.all()) == set(product_variations):

                            user_item.quantity += item.quantity
                            user_item.save()

                            item.delete()
                            matched = True
                            break

                    if not matched:
                        item.user = user
                        item.cart = None
                        item.save()

            except Cart.DoesNotExist:
                pass

            # ---------- LOGIN AFTER MERGE ----------
            auth.login(request, user)

            messages.success(request, "Login Successful")
            return redirect('cart')

        else:
            messages.error(request, "Invalid login credentials")

    return render(request, 'accounts/login.html')




# ----------------------
# REGISTER VIEW
# ----------------------

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password1']

            # Create user
            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=email.split('@')[0],
                password=password,
            )
            user.phone_number = phone_number
            user.is_active = False  # force inactive until email activation
            user.save()

            # Send activation email
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Registration successful. Please check your email to activate your account.')

            # ---------------- CORRECT REDIRECT ----------------
            login_url = reverse('login')  # gives /accounts/login/
            login_url += f'?command=verification&email={email}'  # correct spelling & query string
            return redirect(login_url)

    else:
        form = RegistrationForm()

    context = {'form': form}
    return render(request, 'accounts/register.html', context)


# ----------------------
# LOGOUT
# ----------------------
@login_required(login_url='login')
def logout_user(request):
    auth.logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')

# ----------------------
# DASHBOARD
# ----------------------
@login_required(login_url='login')
def dashboard(request):
    orders =  Order.objects.order_by('created_at').filter(user_id = request.user, is_ordered = True)
    orders_count = orders.count()
    userprofile, created = UserProfile.objects.get_or_create(
        user=request.user
    )
    context = {
        'orders_count' : orders_count,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/dashboard.html',context)

# ----------------------
# ACTIVATE ACCOUNT
# ----------------------
def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated successfully. You can now log in.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')
        return redirect('register')
    
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # Send reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist with this email address.')
            return redirect('forgotPassword')

    return render(request, 'accounts/forgotPassword.html')

def reset_password_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Your password has been reset successfully. You can now log in.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
                return redirect(request.path)

        return render(request, 'accounts/reset_password_confirm.html', {
            'uidb64': uidb64,
            'token': token
        })
    else:
        messages.error(request, 'Password reset link is invalid!')
        return redirect('forgotPassword')

def my_orders(request):
    orders = Order.objects.filter(user = request.user,is_ordered = True).order_by('-created_at')
    context = {
        'orders': orders
    }
    return render(request,'accounts/my_orders.html',context)

@login_required(login_url='login')
def edit_profile(request):

    userprofile = get_object_or_404(UserProfile, user = request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=userprofile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()   # 🔥 no commit=False needed

            messages.success(request, 'Your profile has been updated.')
            return redirect('edit_profile')

    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }

    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            if user.check_password(current_password):
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Your password has been updated successfully.')
                return redirect('change_password')
            else:
                messages.error(request, 'Current password is incorrect.')
                return redirect('change_password')
        else:
            messages.error(request, 'New password and confirm password do not match.')
            return redirect('change_password')

    return render(request, 'accounts/change_password.html')

@login_required(login_url='login')
def order_detail(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
        is_ordered=True
    )

    order_products = OrderProduct.objects.filter(
        order=order
    )
    subtotal = 0
    for item in order_products:
        subtotal += item.product.price * item.quantity

    context = {
        'order_products': order_products,
        'order': order,
        'subtotal': subtotal,
    }

    return render(request, 'accounts/order_detail.html', context)

