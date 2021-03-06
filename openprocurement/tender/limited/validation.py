# -*- coding: utf-8 -*-
from openprocurement.api.validation import validate_data, OPERATIONS
from openprocurement.api.utils import update_logging_context, error_handler, get_now, raise_operation_error  # XXX tender context


def validate_complaint_data(request):
    if not request.check_accreditation(request.tender.edit_accreditation):
        request.errors.add('procurementMethodType', 'accreditation', 'Broker Accreditation level does not permit complaint creation')
        request.errors.status = 403
        raise error_handler(request.errors)
    if request.tender.get('mode', None) is None and request.check_accreditation('t'):
        request.errors.add('procurementMethodType', 'mode', 'Broker Accreditation level does not permit complaint creation')
        request.errors.status = 403
        raise error_handler(request.errors)
    update_logging_context(request, {'complaint_id': '__new__'})
    model = type(request.context).complaints.model_class
    return validate_data(request, model)


def validate_patch_complaint_data(request):
    model = type(request.context.__parent__).complaints.model_class
    return validate_data(request, model, True)

# tender
def validate_chronograph(request):
    if request.authenticated_role == 'chronograph':
        raise_operation_error(request, 'Chronograph has no power over me!')


def validate_update_tender_with_awards(request):
    tender = request.validated['tender']
    if tender.awards:
        raise_operation_error(request, 'Can\'t update tender when there is at least one award.')

# tender document
def validate_operation_with_document_not_in_active_status(request):
    if request.validated['tender_status'] != 'active':
        raise_operation_error(request, 'Can\'t {} document in current ({}) tender status'.format(OPERATIONS.get(request.method), request.validated['tender_status']))

# lot
def validate_lot_operation_not_in_active_status(request):
    tender = request.validated['tender']
    if tender.status != 'active':
        raise_operation_error(request, 'Can\'t {} lot in current ({}) tender status'.format(OPERATIONS.get(request.method), tender.status))


def validate_lot_operation_with_awards(request):
    tender = request.validated['tender']
    if tender.awards:
        raise_operation_error(request, 'Can\'t {} lot when you have awards'.format(OPERATIONS.get(request.method), tender.status))

# award
def validate_award_operation_not_in_active_status(request):
    tender = request.validated['tender']
    if tender.status != 'active':
        raise_operation_error(request, 'Can\'t {} award in current ({}) tender status'.format('create' if request.method == 'POST' else 'update', tender.status))


def validate_create_new_award(request):
    tender = request.validated['tender']
    if tender.awards and tender.awards[-1].status in ['pending', 'active']:
        raise_operation_error(request, 'Can\'t create new award while any ({}) award exists'.format(tender.awards[-1].status))


def validate_lot_cancellation(request):
    tender = request.validated['tender']
    award = request.validated['award']
    if tender.get('lots') and tender.get('cancellations') and [cancellation for cancellation in tender.get('cancellations', []) if cancellation.get('relatedLot') == award.lotID]:
        raise_operation_error(request, 'Can\'t {} award while cancellation for corresponding lot exists'.format(OPERATIONS.get(request.method)))


def validate_create_new_award_with_lots(request):
    tender = request.validated['tender']
    award = request.validated['award']
    if tender.awards:
        if tender.lots:  # If tender with lots
            if award.lotID in [aw.lotID for aw in tender.awards if aw.status in ['pending', 'active']]:
                raise_operation_error(request, 'Can\'t create new award on lot while any ({}) award exists'.format(tender.awards[-1].status))
        else:
            validate_create_new_award(request)

# award document
def validate_document_operation_not_in_active(request):
    if request.validated['tender_status'] != 'active':
        raise_operation_error(request, 'Can\'t {} document in current ({}) tender status'.format(OPERATIONS.get(request.method), request.validated['tender_status']))


def validate_award_document_add_not_in_pending(request):
    if request.validated['award'].status != 'pending':
        raise_operation_error(request, 'Can\'t add document in current ({}) award status'.format(request.validated['award'].status))

# award complaint
def validate_award_complaint_operation_not_in_active(request):
    tender = request.validated['tender']
    if tender.status != 'active':
        raise_operation_error(request, 'Can\'t {} complaint in current ({}) tender status'.format(OPERATIONS.get(request.method), tender.status))

# contract
def validate_contract_operation_not_in_active(request):
    if request.validated['tender_status'] not in ['active']:
        raise_operation_error(request, 'Can\'t {} contract in current ({}) tender status'.format(OPERATIONS.get(request.method), request.validated['tender_status']))


def validate_contract_update_in_cancelled(request):
    if request.context.status == 'cancelled':
        raise_operation_error(request, 'Can\'t update contract in current ({}) status'.format(request.context.status))


def validate_contract_with_cancellations_and_contract_signing(request):
    data = request.validated['data']
    if request.context.status != 'active' and 'status' in data and data['status'] == 'active':
        tender = request.validated['tender']
        award = [a for a in tender.awards if a.id == request.context.awardID][0]
        if tender.get('lots') and tender.get('cancellations') and [cancellation for cancellation in tender.get('cancellations') if cancellation.get('relatedLot') == award.lotID]:
            raise_operation_error(request, 'Can\'t update contract while cancellation for corresponding lot exists')
        stand_still_end = award.complaintPeriod.endDate
        if stand_still_end > get_now():
            raise_operation_error(request, 'Can\'t sign contract before stand-still period end ({})'.format(stand_still_end.isoformat()))
        if any([
            i.status in tender.block_complaint_status and a.lotID == award.lotID
            for a in tender.awards
            for i in a.complaints
        ]):
            raise_operation_error(request, 'Can\'t sign contract before reviewing all complaints')


# contract document
def validate_contract_document_operation_not_in_allowed_contract_status(request):
    contract = request.validated['contract']
    if contract.status not in ['pending', 'active']:
        raise_operation_error(request, 'Can\'t {} document in current contract status'.format(OPERATIONS.get(request.method)))

#cancellation
def validate_cancellation_in_termainated_status(request):
    tender = request.validated['tender']
    if tender.status in ['complete', 'cancelled', 'unsuccessful']:
        raise_operation_error(request, 'Can\'t {} cancellation in current ({}) tender status'.format(OPERATIONS.get(request.method), tender.status))
