from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from knox.models import AuthToken

admin.site.unregister(Group)
admin.site.unregister(AuthToken)
admin.site.unregister(EmailAddress)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialToken)
admin.site.unregister(Site)

admin.site.site_header = "Welcome to Apart - Administrador"
admin.site.index_title = "Apart - Administrator"
admin.site.site_title = "Apart - Admin Portal"
