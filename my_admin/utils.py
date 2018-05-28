from django.db.models import Q


def table_filter(request, admin_class):
    filter_conditions = {}
    keywords = ['page', 'o', 'q']
    for k,v in request.GET.items():
        if k in keywords:
            continue
        if v:
            filter_conditions[k] = v

    return admin_class.real_model.objects.filter(**filter_conditions),filter_conditions

def table_search(request, admin_class, obj_list):
    search_key = request.GET.get('q','')
    q_obj = Q()
    q_obj.connector = 'OR'
    for col in admin_class.search_fields:
        q_obj.children.append(('%s__contains' %col, search_key))

    obj_list = obj_list.filter(q_obj)
    return obj_list

def table_sort(request, obj_list):
    order_key = request.GET.get('o')
    if order_key:
        res = obj_list.order_by(order_key)
        if order_key.startswith('-'):
            order_key = order_key.strip('-')
        else:
            order_key = '-%s'%order_key
    else:
        res = obj_list
    return res, order_key
