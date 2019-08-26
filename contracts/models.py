from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now


class Vendor(models.Model):
    user = models.ManyToManyField(User)
    name = models.CharField(max_length=30, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class File(models.Model):
    file = models.FileField(upload_to='documents/')

    def __str__(self):
        return self.file.name


class Contract(models.Model):
    approved = 1
    pending = 0
    vendor = 2
    STATUS_CHOICES = (
        (approved, 'Approved'),
        (vendor, 'Vendors Approved'),
        (pending, 'Pending'),
    )
    smart_choices = ((1, 'Yes'), (0, 'No'))
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    installments = models.IntegerField(null=True)
    amount_paid = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    status = models.CharField(max_length=2,
                                 choices=STATUS_CHOICES, default=0, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    validity = models.DateField(default=now())
    comments = models.TextField(null=True, blank=True)
    smart_contract = models.BooleanField(max_length=2, choices=smart_choices, default=0)
    files = models.ManyToManyField(File, related_name='files')
    hash_key = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Approvals(models.Model):
    LEVEL_CHOICES = (
        ('0', 'Contract'),
        ('1', 'Sow'),
        ('2', 'Invoice'),
    )
    Approvals = ((1, 'Yes'), (0, 'No'))
    contracts = models.ForeignKey(Contract, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    status = models.BooleanField(max_length=2, choices=Approvals, default=0)
    comments = models.TextField(null=True, blank=True)
    contract_level = models.CharField(max_length=2,
                                 choices=LEVEL_CHOICES, default=0, null=True, blank=True)

    def __str__(self):
        return self.contracts.name


class DocuSign(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    envelope = models.CharField(max_length=255, null=True, blank=True)
    document_name = models.CharField(max_length=255, null=True, blank=True)
    files = models.FileField(upload_to='media/', null=True, blank=True)

    def __str__(self):
        return self.contract.name


class IPFSModel(models.Model):
    name = models.CharField(max_length=255)
    hashkey = models.CharField(max_length=255)
    size = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class Sow(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE,null=True)
    smart_choices = ((1, 'Yes'), (0, 'No'))
    smart_contract = models.BooleanField(max_length=2, choices=smart_choices, default=0)
    file = models.FileField(upload_to='documents/')

    def __str__(self):
        return self.contract.name


class Invoice(models.Model):
    amount = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE,null=True)
    file = models.FileField(upload_to='documents/')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    smart_choices = (('1', 'Declined'), ('0', 'Approved'), ('2', 'Created'))
    status = models.CharField(max_length=2, choices=smart_choices, default='2', null=True, blank=True)
   
    def __str__(self):
        return self.contract.name
