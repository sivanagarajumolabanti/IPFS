import shutil
import os
import base64

from django.conf import settings
from docusign_esign import (
    ApiClient, EnvelopesApi, EnvelopeDefinition, Signer, SignHere,
    Tabs, Recipients, Document, RecipientViewRequest
)

from contracts.models import DocuSign


def envelope_obj():
    api_client = ApiClient()
    privatekey = os.path.join(settings.BASE_DIR, "keys", "private_key")
    api_client.host = settings.DOCU_BASE_URL
    api_client.configure_jwt_authorization_flow(
        privatekey, settings.DOCU_OAUTH_BASE_URL, settings.DOCU_INTEGRATOR_KEY,
        settings.DOCU_ACCOUNT_USERNAME, 5001)
    return EnvelopesApi(api_client)


def embedded_signing_ceremony(filename, vname, vemail):
    """
    The document <file_name> will be signed by <signer_name> via an
    embedded signing ceremony.
    """

    #
    # Step 1. The envelope definition is created.
    #         One signHere tab is added.
    #         The document path supplied is relative to the working directory
    #
    # Create the component objects for the envelope definition...

    with open(filename, "rb") as file:
        content_bytes = file.read()
    base64_file_content = base64.b64encode(content_bytes).decode('ascii')

    document = Document(
        document_base64=base64_file_content,
        name='IPFS Document',  # can be different from actual file name
        file_extension='pdf',  # many different document types are accepted
        document_id=1  # a label used to reference the doc
    )

    # Create the signer recipient model
    signer = Signer(
        email=vemail, name=vname, recipient_id="1", routing_order="1",
        client_user_id=settings.DOCU_CLIENT_ID)

    sign_here = SignHere(document_id='1', page_number='1', recipient_id='1',
                         tab_label='IPFS Sign Request', x_position='200', y_position='147')

    # Add the tabs model (including the sign_here tab) to the signer
    signer.tabs = Tabs(sign_here_tabs=[sign_here])  # The Tabs object wants arrays of the different field/tab types

    # Next, create the top level envelope definition and populate it.
    envelope_definition = EnvelopeDefinition(email_subject="Please sign this document sent from IPFS",
        documents=[document], recipients=Recipients(signers=[signer]), status="sent")

    envelope_api = envelope_obj()
    results = envelope_api.create_envelope(settings.DOCU_ACCOUNT_ID, envelope_definition=envelope_definition)

    envelope_id = results.envelope_id
    recipient_view_request = RecipientViewRequest(
        authentication_method=settings.DOCU_AUTH_METHOD, client_user_id=settings.DOCU_CLIENT_ID,
        recipient_id='1', return_url=settings.DOCU_REDIRECT_URL, user_name=vname, email=vemail)

    results = envelope_api.create_recipient_view(settings.DOCU_ACCOUNT_ID, envelope_id,
                                                 recipient_view_request=recipient_view_request)
    return results.url, envelope_id


def get_envelope_by_id(envelope_id):
    envelope_api = envelope_obj()
    results = envelope_api.get_envelope(settings.DOCU_ACCOUNT_ID, envelope_id)
    return results


def download_attachment(envelope_id):
    envelope_api = envelope_obj()
    result = envelope_api.get_document(settings.DOCU_ACCOUNT_ID, 'combined', envelope_id)
    file_name = "%s.pdf" % envelope_id.replace("-","_")

    shutil.move(result, os.path.join(settings.MEDIA_ROOT, 'media', file_name))
    dc_obj = DocuSign.objects.get(envelope=envelope_id)
    dc_obj.document_name = file_name
    dc_obj.files.name = "media/%s" % file_name
    dc_obj.save()

    return dc_obj.contract.id
