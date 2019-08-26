from django.contrib import admin
from .models import *


class ContractAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'created_at', 'status')
    list_filter = ('status',)


admin.site.register(Contract, ContractAdmin)

admin.site.register(Vendor)
admin.site.register(Approvals)
admin.site.register(File)
admin.site.register(Sow)
# admin.site.register(UserContracts)
admin.site.register(DocuSign)