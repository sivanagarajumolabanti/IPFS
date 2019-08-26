from django.db import models

# Create your models here.


class IPFSConfiguration(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    url = models.URLField(verbose_name='IPFS Server IP Address')
    port = models.CharField(max_length=10, default=5000)

    def __str__(self):
        return self.url


class DocuSignConfiguration(models.Model):
    username = models.CharField(max_length=200)
    accesstoken = models.CharField(max_length=500)
    account_id = models.CharField(max_length=200)
    account_username = models.CharField(max_length=200)
    redirecturl = models.URLField()
    baseurl = models.URLField()
    integratorkey = models.CharField(max_length=200)
    oauthbaseurl = models.URLField()
    clientid = models.CharField(max_length=200, default='123')
    authmethod = models.CharField(max_length=200, default='None')

    def __str__(self):
        return self.username


class BlockChain(models.Model):
    url = models.URLField()

    def __str__(self):
        return self.url
