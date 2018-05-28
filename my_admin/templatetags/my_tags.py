from django.template import Library
from django.utils.safestring import mark_safe
from django.utils.timezone import datetime,timedelta   # 使用的是setting里设置时区的时间
from django.core.exceptions import FieldDoesNotExist

register = Library()

@register.simple_tag
def build_rows(request,obj,admin_class):
    row_ele = ''
    for index,col in enumerate(admin_class.list_display):
        try:
            field_obj = obj._meta.get_field(col)
            if field_obj.choices:  # 如果是choices type
                # getattr(obj,get_source_display)()
                col_data = getattr(obj,"get_%s_display" % col)()
            else:
                # getattr(obj,'xx') <=> obj.xx
                col_data = getattr(obj, col)

            if type(col_data).__name__ == 'datetime':
                col_data = col_data.strftime("%Y-%m-%d %H:%M:%S")  # 转换时间格式

            if index == 0:
                col_data = "<a href='{request_path}{obj_id}/change/'>{data}</a>".format(request_path=request.path,
                                                                                           obj_id=obj.id,
                                                                                           data=col_data)
        # For 自定义字段 enroll
        except FieldDoesNotExist as e :
            if hasattr(admin_class,col):
                column_func = getattr(admin_class,col)
                admin_class.instance = obj
                admin_class.request = request
                col_data = column_func()

        row_ele += "<td>%s</td>" % col_data

    return mark_safe(row_ele)


@register.simple_tag
def build_cols(col, order_key, filter_conditions, search_text):
    filters = ''
    for k, v in filter_conditions.items():
        filters += "&%s=%s" % (k, v)

    ele = '''<th><a href="?{filters}&o={sort_key}&q={search_key}">{column}</a>{sort_icon}</th>'''
    if order_key:
        if order_key.startswith("-"):
            sort_icon = '''<span class="glyphicon glyphicon-chevron-up"></span>'''
        else:
            sort_icon = '''<span class="glyphicon glyphicon-chevron-down"></span>'''

        if order_key.strip("-") == col:  # 排序的就是这个字段
            sort_key = order_key
        else:
            sort_key = col
            sort_icon = ''

    else:  # 没有排序
        sort_key = col
        sort_icon = ''

    ele = ele.format(sort_key=sort_key, column=col,sort_icon=sort_icon,filters=filters,search_key=search_text)
    return mark_safe(ele)


@register.simple_tag
def build_paginators(query_sets, filter_conditions, last_order, search_text):
    '''返回整个分页元素'''
    filters = ''
    for k, v in filter_conditions.items():
        filters += "&%s=%s" % (k, v)

    page_tags = ''
    if query_sets.has_previous():
        page_tags += '''<li class=""><a href="?page=%s%s&o=%s&q=%s">上页</a></li>''' % (
        query_sets.previous_page_number(), filters, last_order, search_text)

    added_dot_ele = False
    for page_num in query_sets.paginator.page_range:
        # 判断是否在前两页,后两页,或者前后一页
        if page_num < 3 or page_num > query_sets.paginator.num_pages - 2 or abs(query_sets.number - page_num) <= 2:
            ele_class = ""
            if query_sets.number == page_num:
                added_dot_ele = False
                ele_class = "active"
                page_tags += '''<li class="%s"><a href="?page=%s%s&o=%s&q=%s">%s</a></li>''' % (
                ele_class, page_num, filters, last_order, search_text, page_num)
        else:  # 显示...
            if not added_dot_ele:  # 如果还没加...
                page_tags += '<li><a>...</a></li>'
                added_dot_ele = True

    if query_sets.has_next():
        page_tags += '''<li class=""><a href="?page=%s%s&o=%s&q=%s">下页</a></li>''' % (
        query_sets.next_page_number(), filters, last_order, search_text)

    return mark_safe(page_tags)

@register.simple_tag
def render_filter_ele(filter_field, admin_class, filter_conditions):
    select_ele = '''<select class="form-control" name='{filter_field}' ><option value=''>----</option>'''
    field_obj = admin_class.real_model._meta.get_field(filter_field)
    if field_obj:
        selected = ''
        for choice_item in field_obj.choices:  # ((0,'QQ'),(1,'baidu'),)
            # print("choice",choice_item,filter_conditions.get(filter_field),type(filter_conditions.get(filter_field)))
            if str(choice_item[0]) == filter_conditions.get(filter_field):
                selected = 'selected'
            select_ele += '''<option value='%s' %s>%s</option>''' % (choice_item[0], selected, choice_item[1])
            selected = ''

    if type(field_obj).__name__ == "ForeignKey":
        selected = ''
        for choice_item in field_obj.get_choices()[1:]:
            if str(choice_item[0]) == filter_conditions.get(filter_field):
                selected = 'selected'
            select_ele += '''<option value='%s' %s>%s</option>''' % (choice_item[0], selected, choice_item[1])
            selected = ''

    if type(field_obj).__name__ in ['DateTimeField','DateField']:
        date_els = []
        today_ele = datetime.now().date()
        date_els.append(['今天', datetime.now().date()])
        date_els.append(["昨天",today_ele - timedelta(days=1)])
        date_els.append(["近7天",today_ele - timedelta(days=7)])
        date_els.append(["本月",today_ele.replace(day=1)])   # month to day
        date_els.append(["近30天",today_ele - timedelta(days=30)])
        date_els.append(["近90天",today_ele - timedelta(days=90)])
        date_els.append(["近180天",today_ele - timedelta(days=180)])
        date_els.append(["本年",today_ele.replace(month=1,day=1)])   # year to day
        date_els.append(["近一年",today_ele  - timedelta(days=365)])
        selected = ''
        for item in date_els:
            # print('choice: ',type(item[1]),item[1],type(filter_conditions.get('date__gte')),filter_conditions.get('date__gte'))
            if str(item[1]) == filter_conditions.get('date__gte'):
                selected = 'selected'
            select_ele += '''<option value='%s' %s>%s</option>''' %(item[1],selected,item[0])
            selected = ''

        filter_field_name = "%s__gte" % filter_field  # gte 大于等于

    else:
        filter_field_name = filter_field
    select_ele += "</select>"
    select_ele = select_ele.format(filter_field=filter_field_name)

    return mark_safe(select_ele)

@register.simple_tag
def get_m2m_obj_list(admin_class,field,model_form_obj):
    '''(左)返回m2m所有待选数据'''
    # 表结构对象的某个字段
    field_obj = getattr(admin_class.real_model,field.name)
    # print(field_obj,type(field_obj),field.name)  #<django.db.models.fields.related_descriptors.ManyToManyDescriptor object at 0x1086309b0> <class 'django.db.models.fields.related_descriptors.ManyToManyDescriptor'> tags
    all_obj_list = field_obj.rel.model.objects.all()  # tags里的所有对象

    # 判断instance是否为空
    if model_form_obj.instance.id:
        obj_instance_field = getattr(model_form_obj.instance, field.name) # 单条数据的tags里的所有对象
        selected_obj_list = obj_instance_field.all()  # 已选择的数据

    else:  # 代表这是在添加新的一条记录
        return all_obj_list

    standby_obj_list = []
    for obj in all_obj_list:
        if obj not in selected_obj_list:
            standby_obj_list.append(obj)

    return standby_obj_list


@register.simple_tag
def get_m2m_selected_obj_list(model_form_obj,field):
    '''(右)返回已选择的m2m数据'''
    if model_form_obj.instance.id :
        obj_instance_field = getattr(model_form_obj.instance,field.name)
        return obj_instance_field.all()


def recursive_related_objs_lookup(objs):
    ul_ele = "<ul>"
    for obj in objs:
        print(obj,'!!!!!!!??????????')
        li_ele = '''<li> %s: %s </li>'''%(obj._meta.verbose_name, obj.__str__().strip("<>"))
        ul_ele += li_ele

        # for local many to many
        for m2m_field in obj._meta.local_many_to_many: #把所有跟这个对象直接关联的m2m字段取出来了
            sub_ul_ele = "<ul>"
            m2m_field_obj = getattr(obj,m2m_field.name)   #getattr(models.Customer.objects.all().first(), 'tags')
            for o in m2m_field_obj.select_related():  # customer.tags.select_related()
                li_ele = '''<li> %s: %s </li>''' % (m2m_field, o.__str__().strip("<>"))
                sub_ul_ele += li_ele

            sub_ul_ele += '</ul>'
            ul_ele += sub_ul_ele

        # for ManyToOneRel
        for related_obj in obj._meta.related_objects:
            if 'ManyToManyRel' in related_obj.__repr__():

                if hasattr(obj,related_obj.get_accessor_name()):  # hassattr(models.Customer.objects.all().first(),'enrollment_set')
                    accessor_obj = getattr(obj, related_obj.get_accessor_name())    # accessor_obj 相当于 customer.enrollment_set
                    if hasattr(accessor_obj, 'select_related'):  # slect_related() == all()
                        target_objs = accessor_obj.select_related()  # target_objs 相当于 customer.enrollment_set.all()

                        sub_ul_ele = "<ul style='color:red'>"
                        for o in target_objs:
                            li_ele = '''<li> %s: %s </li>''' % (o._meta.verbose_name, o.__str__().strip("<>"))
                            sub_ul_ele += li_ele
                        sub_ul_ele += "</ul>"
                        ul_ele += sub_ul_ele

            elif hasattr(obj, related_obj.get_accessor_name()):
                accessor_obj = getattr(obj, related_obj.get_accessor_name())
                if hasattr(accessor_obj, 'select_related'):
                    target_objs = accessor_obj.select_related()
                else:
                    target_objs = accessor_obj

                if len(target_objs) > 0:
                    nodes = recursive_related_objs_lookup(target_objs)
                    ul_ele += nodes

    ul_ele +="</ul>"
    return ul_ele


@register.simple_tag
def display_related_obj(objs):
    '''把对象及所有相关联的数据取出来'''
    # print(type(objs).__name__,objs.__str__,'**************************************8')
    if type(objs).__name__ != 'QuerySet':
        objs = [objs,]  # if not multiple delete
    if objs:
        # model_class = objs[0]._meta.model
        # mode_name = objs[0]._meta.model_name
        return mark_safe(recursive_related_objs_lookup(objs))


@register.simple_tag
def get_action_verbose_name(admin_class,action):
    action_func = getattr(admin_class,action)
    return  action_func.display_name if hasattr(action_func,'display_name') else action