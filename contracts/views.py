import random
import string
import requests
import ipfsapi
import json


from django.db.models import Q
from django.contrib.auth import logout
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from contracts.forms import *
from contracts.docusign import embedded_signing_ceremony, get_envelope_by_id, download_attachment
from contracts.generate_pdf import call_pdf
from Configuration.models import IPFSConfiguration


def get_contracts(user):
    return set(Contract.objects.filter(
        Q(user=user) | Q(vendor__user__in=[user])).values_list('id', flat=True))


@login_required
def home(request):
    contract = len(get_contracts(request.user))
    vendor = Vendor.objects.filter(user=request.user).count()
    pending_approvals = Approvals.objects.filter(user=request.user, status=0).count()
    return render(
        request, 'dashboard.html',
        {'contract': contract, 'vendor': vendor, 'pending_approvals': pending_approvals}
    )


@login_required
def contracts(request):
    storage = messages.get_messages(request)
    success = None

    for msg in storage:
        success = msg

    cids = get_contracts(request.user)
    contract = Contract.objects.filter(id__in=cids)
    return render(request, "contracts.html", dict(contract=contract, success=success))


@login_required
def vendors(request):
    vendor = Vendor.objects.filter(user=request.user)
    return render(request, "vendors.html", {'vendor': vendor})


@login_required
def profile(request):
    return render(request, 'profile.html')


@login_required
def createvendor(request):
    if request.method == "POST":
        data = request.POST.copy()
        data['user'] = request.user.id
        form = VendorForm(data)
        if form.is_valid():
            form.save()
        return redirect(vendors)
    else:
        form = VendorForm()
    return render(request, 'createvendor.html', {'form': form})


@login_required
def createcontract(request):
    if request.method == "POST":
        data = request.POST.copy()
        data['user'] = request.user.id
        data['status'] = 0
        form = ContractForm(data, request.FILES)

        if form.is_valid():
            ct = form.save()
            messages.add_message(request, messages.INFO, "Data Saved Successfully")
            files = request.FILES.getlist('files')

            for fl in files:
                ct.files.create(file=fl)
            vend = Vendor.objects.get(id=request.POST['vendor'])
            for user in vend.user.all():
                apform = ApprovalForm(
                    {'contracts': ct.pk, 'user': user.id, 'status': 0, 'contract_level': 0}
                )
                if apform.is_valid():
                    apform.save()
        else:
            messages.add_message(request, messages.ERROR, "Error while creating contract")
        return redirect(contracts)
    else:
        form = ContractForm()
    return render(request, 'createcontract.html', {'form': form})


@login_required
def pendingapprovals(request):
    data = Approvals.objects.filter(user=request.user)
    return render(request, 'approvals.html', {'data': data})


def update_to_ipfs_chains(contracts):
    # Logic to connect to IPFS and Blockchain
    print("Logic Called for posting data to IPFS......")
    ipfs_details = IPFSConfiguration.objects.all()[0]
    api = ipfsapi.connect(ipfs_details.url, int(ipfs_details.port))
    filename = contracts.files.all()[0]
    new_file = api.add(filename.file.path)
    print(new_file)

    IPFSModel.objects.create(
        name=new_file['Name'], hashkey=new_file['Hash'],
        size=new_file['Size'])

    # new_add is the variable from ipfs
    dhash = new_file['Hash']
    dname = new_file['Name']

    headers = {'Content-Type': 'application/json'}

    bdata = {
        "contractID": str(contracts.id),
        "Party1ID": "Party1ID",
        "Party2ID": "Party2ID",
        "amount": int(contracts.amount),
        "installments": int(contracts.installments),
        "amountPaid": int(contracts.amount_paid),
        "documents": [{"docName": dname, "docHash": dhash}]
    }
    print(json.dumps(bdata))
    r = requests.post(settings.BLOCKCHAINURL, headers=headers, data=json.dumps(bdata))


@login_required
def getapproval(request, pk):
    data = Approvals.objects.get(id=pk)
    if request.method == 'POST':
        if data.get_status_display() != request.POST['status']:
            data.status = 1 if request.POST['status'] == "Yes" else 0
            data.save()
        all_status = Approvals.objects.filter(contracts=data.contracts).values_list('status', flat=True)
        if False not in all_status:
            data.contracts.status = 1
            data.contracts.save()
        return redirect(pendingapprovals)
    return render(request, 'post_approve.html', {'data': data})


@login_required
def get_contract_status(request):
    envelope_id = request.session['docu_envelope']
    data = get_envelope_by_id(envelope_id)
    if data.status == 'completed':
        contract = download_attachment(envelope_id)
        obj = Approvals.objects.filter(user=request.user, status=0, contracts=contract)
        obj.update(status=1)
        all_status = Approvals.objects.filter(contracts__id=contract).values_list('status', flat=True)
        if False not in all_status:
            cnt = Contract.objects.filter(id=contract)
            if request.user == cnt[0].user:
                cnt.update(status="1")
                update_to_ipfs_chains(cnt[0])
            else:
                cnt.update(status="2")
    return redirect(contracts)


@login_required
def createsow(request, pk):
    # data = Contract.objects.get(id=pk)
    if request.method == 'POST':
        if request.POST.get('submit') == 'Sow_approve':
            # test
            Approvals.objects.filter(user=request.user, status=0, contracts=pk)
            sow = Sow.objects.get(contract=pk)
            
            url, envelope = embedded_signing_ceremony(sow.file.path, request.user.get_full_name(), request.user.email)
            request.session['docu_envelope'] = envelope
            docuform = DocuSignForm({'user': request.user.id, 'envelope': envelope, 'contract': pk})
            if docuform.is_valid():
               docuform.save()

            return redirect(url)

        messages.add_message(request, messages.INFO, "Data Saved Successfully")
        postdata = request.POST.copy()
        postdata['contract'] = pk
        form = SowForm(postdata, request.FILES)
        if form.is_valid():
            form.save()
            vend = Vendor.objects.get(name=request.POST['vendor'])
            for user in vend.user.all():
                apform = ApprovalForm({
                    'contracts': pk, 'user': user.id, 'status': 0, 'contract_level': 1
                })
                if apform.is_valid():
                    apform.save()
        else:
            messages.add_message(request, messages.ERROR, "Error while creating contract")

    return redirect('detailedcontract', pk=pk)


@login_required
def invoicedecline(request, pk):
    data = Invoice.objects.get(id=pk)
    data.status = '1'
    data.save()
    return redirect('detailedcontract', pk=data.contract.id)


@login_required
def invoiceapprove(request, pk):
    data = Invoice.objects.get(id=pk)
    data.status = '0'
    data.save()
    return redirect('detailedcontract', pk=data.contract.id)


@login_required
def getinvoice(request, pk):
    data = Contract.objects.get(id=pk)
    if request.method == 'POST':
        postdata = request.POST.copy()
        if postdata.get('submit') == 'invoice_submit':
            postdata['user'] = request.user.id
            postdata['contract'] = pk
            postdata['status'] = 2
            form = InvoiceForm(postdata, request.FILES)
            if form.is_valid():
                form.save()
    return redirect('detailedcontract', pk=pk)


@login_required
def get_contract(request, pk):
    data = Contract.objects.get(id=pk)
    if request.method == 'POST':
        postdata = request.POST.copy()

        if request.POST.get('submit') == 'approval_return':
            return redirect(contracts)

        if request.POST.get('submit') == 'admin_submit' and postdata['smart_contract']:
            if postdata.get('declined_contract') == 'on':
                data.status = 0
                obj = Approvals.objects.filter(contracts=pk)
                obj.update(status=0)
            else:
                obj = Approvals.objects.filter(user=request.user, status=0, contracts=pk)
                obj.update(status=1, comments=postdata.get('apprcomments'))
                all_status = Approvals.objects.filter(contracts__id=pk).values_list('status', flat=True)
                if False not in all_status:
                    data.status = 2
                if False not in all_status and request.user == data.user:
                    data.status = 1
                    #update_to_ipfs_chains(data)
            data.save()
            return redirect(contracts)

        if postdata.get('declined_contract') == 'on':
            data.comments = postdata.get('apprcomments')
            
            obj = Approvals.objects.filter(contracts=pk)
            obj.update(status=0)
            
            data.status = 0
            data.save()
            return redirect(contracts)

        if request.FILES:
            x = ''.join(
                random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
                for _ in range(16))
            postdata['hash_key'] = x

            form = UpdatedContractForm(postdata, request.FILES, instance=data)
            if form.is_valid():
                ct = form.save()
                files = request.FILES.getlist('file')
                for fl in files:
                    ct.files.create(file=fl)

        if request.POST.get('submit') == 'admin_submit':
            return redirect(contracts)

        pdf_file = call_pdf(postdata)
        obj = Approvals.objects.filter(user=request.user, status=0, contracts=pk)
        obj.update(comments=postdata.get('apprcomments'))

        url, envelope = embedded_signing_ceremony(pdf_file, request.user.get_full_name(), request.user.email)
        request.session['docu_envelope'] = envelope
        docuform = DocuSignForm({'user': request.user.id, 'envelope': envelope, 'contract': data.id})
        if docuform.is_valid():
            docuform.save()

        return redirect(url)
    else:
        approval = Approvals.objects.filter(user=request.user, status=1, contracts=pk)
        all_approvals = Approvals.objects.filter(contracts=pk).values_list('status', flat=True)
        all_approved = True if False not in all_approvals else False

        contact_approval = Approvals.objects.filter(contracts=pk)
        approve = True if approval else False
        form = ContractForm(instance=data)
        docu = DocuSign.objects.filter(contract=data.id)
        sow = Sow.objects.filter(contract=data.id)

        if request.user in data.vendor.user.all():
            invoices = Invoice.objects.filter(contract=pk, user=request.user)
        else:
            invoices = Invoice.objects.filter(contract=pk)
        if sow:
            sow = sow[0]

    return render(
        request, 'detailedcontract.html',
        dict(form=form, data=data, docusign=docu, approval=approve,
             approvals=contact_approval, all_approve=all_approved,
             sow=sow, invoices=invoices)
    )


def logout_view(request):
    logout(request)
    return redirect('home')
