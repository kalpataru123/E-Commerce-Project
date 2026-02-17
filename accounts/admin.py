from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account,UserProfile
from django.utils.html import format_html

# Register your models here.

class AccountAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_admin', 'is_active')
    search_fields = ('email', 'username')
    readonly_fields = ('date_joined', 'last_login')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

class UserProfileAdmin(admin.ModelAdmin):

    def thumbnail(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="30" style="border-radius:50%;">',
                obj.profile_picture.url
            )
        return "No Image"

    thumbnail.short_description = "Profile Picture"
    list_display = ('thumbnail', 'user', 'city', 'state', 'country')


admin.site.register(Account, AccountAdmin)
admin.site.register(UserProfile,UserProfileAdmin)