from django.contrib import admin
from .models import IPFSConfiguration, DocuSignConfiguration
# Register your models here.


admin.site.register(IPFSConfiguration)
admin.site.register(DocuSignConfiguration)
