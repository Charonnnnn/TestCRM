from django.shortcuts import render,redirect
from my_admin import my_admin
from django.core.paginator import Paginator
from my_admin import utils
from my_admin import forms

def table_index(request):
    # print(my_admin.enable_admins)
    return render(request, 'my_admin/table_index.html', {'table_list': my_admin.enable_admins})


def table_objs(request, app_name, model_name):
    admin_class = my_admin.enable_admins[app_name][model_name]
    # obj_list = admin_class.real_model.objects.all()

    # For action
    if request.method == "POST":  # action 来了
        selected_ids = request.POST.get("selected_ids")
        action = request.POST.get("action")
        if selected_ids:
            selected_objs = admin_class.real_model.objects.filter(id__in=selected_ids.split(','))
        else:
            raise KeyError("No object selected.")
        if hasattr(admin_class, action):
            action_func = getattr(admin_class, action)
            request._admin_action = action
            return action_func(admin_class, request, selected_objs)

    obj_list, filter_conditions = utils.table_filter(request, admin_class)  # 过滤后的结果
    # print(filter_conditions)
    obj_list = utils.table_search(request, admin_class, obj_list)  # 搜索后的结果
    obj_list, order_key = utils.table_sort(request, obj_list)  # 排序后的结果
    # print(obj_list, order_key)

    paginator = Paginator(obj_list, admin_class.list_per_page)
    page = request.GET.get('page')
    query_sets = paginator.get_page(page)

    return render(request, 'my_admin/table_objs.html', {'admin_class': admin_class,
                                                        'model_name': model_name,
                                                        'query_sets': query_sets,
                                                        'filter_conditions': filter_conditions,
                                                        'search_text': request.GET.get('q', ''),
                                                        'order_key': order_key,
                                                        'last_order': request.GET.get('o', ''),
                                                        })

def table_obj_change(request, app_name, model_name, obj_id):
    # print(app_name,model_name,obj_id)
    admin_class = my_admin.enable_admins[app_name][model_name]
    model_form_class = forms.create_model_form(request, admin_class)

    obj = admin_class.real_model.objects.get(id=obj_id)
    if request.method == 'POST':
        model_form_obj = model_form_class(request.POST, instance=obj)  # 更新, 要是没有instance=obj就变成创建了!!
        if model_form_obj.is_valid():
            model_form_obj.save()
            return redirect('/my_admin/%s/%s/' % (app_name, model_name))

    else:  #GET
        model_form_obj = model_form_class(instance=obj)  # 创建

    return render(request, 'my_admin/table_obj_change.html', {'model_form_obj': model_form_obj,
                                                             'admin_class': admin_class,
                                                             'app_name': app_name,
                                                             'model_name': model_name,
                                                             'change_delete_add': 'change',
                                                             })


def table_obj_add(request,app_name,model_name):
    admin_class = my_admin.enable_admins[app_name][model_name]
    is_add_form = True
    model_form_class = forms.create_model_form(request, admin_class)

    if request.method == 'POST':
        model_form_obj = model_form_class(request.POST)
        if model_form_obj.is_valid():
            model_form_obj.save()
            return redirect(request.path.replace('/add/', '/'))
    else:
        model_form_obj = model_form_class()
    return render(request,'my_admin/table_obj_add.html',{'model_form_obj': model_form_obj,
                                                             'admin_class': admin_class,
                                                             'change_delete_add': 'add',
                                                             })

def table_obj_delete(request,app_name,model_name,obj_id):
    admin_class = my_admin.enable_admins[app_name][model_name]
    obj = admin_class.real_model.objects.get(id=obj_id)

    if admin_class.readonly_table:
        errors = {"readonly_table": "table is readonly ,obj [%s] cannot be deleted" % obj}
    else:
        errors = {}

    if request.method == "POST":
        if not admin_class.readonly_table:
            obj.delete()
            return redirect("/my_admin/%s/%s/" % (app_name, model_name))

    return render(request, 'my_admin/table_obj_delete.html', {'obj': obj,
                                                             'admin_class': admin_class,
                                                             "app_name": app_name,
                                                             "model_name": model_name,
                                                             'errors': errors,
                                                             })