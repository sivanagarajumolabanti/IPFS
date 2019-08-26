from django import forms
from .models import *


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ("name", "user")


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = (
            "user", "name", "vendor", "amount", "amount_paid", "installments",
            "comments", "validity", "smart_contract"
        )


class UpdatedContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ("amount_paid", "installments", "comments")


class ApprovalForm(forms.ModelForm):
    class Meta:
        model = Approvals
        fields = "__all__"


class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = "__all__"


class DocuSignForm(forms.ModelForm):
    class Meta:
        model = DocuSign
        fields = ("contract", "envelope", "user")


class SowForm(forms.ModelForm):
    class Meta:
        model = Sow
        # fields = ("contract", "smart_contract", "file")
        fields = "__all__"


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = "__all__"
   

# class DocuSignUpdateForm(forms.ModelForm):
#     class Meta:
#         model = DocuSign
#         fields = "document_name"
