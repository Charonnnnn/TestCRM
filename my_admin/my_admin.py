from crm import models
from django.shortcuts import render, redirect, HttpResponse

'''
{'crm':
    {'UserProfile':UserProfileAdmin},  # key是model的名字, value是自定义admin_class
    {'Customer':CustomerAdmin}
}
'''
enable_admins = {}

class BaseAdmin:
    list_display = []
    list_filters = []
    list_per_page = 20
    search_fields = []
    ordering = None
    filter_horizontal = []
    readonly_fields = []
    readonly_table = False
    modelform_exclude_fields = []

    actions = ['delete_selected_objs', ]

    def delete_selected_objs(self, request, querysets):
        # print('*******>>>>delete_selected_objs',self,request,querysets)  #*******>>>>delete_selected_objs <class 'my_admin.my_admin.CustomerAdmin'> <WSGIRequest: POST '/my_admin/crm/customer/'> <QuerySet [<Customer: bbbb>, <Customer: cccc>]>

        app_name = self.real_model._meta.app_label
        table_name = self.real_model._meta.model_name

        if self.readonly_table:
            errors = {"readonly_table": "This table is readonly ,cannot be deleted or modified!"}
        else:
            errors = {}

        if request.POST.get("delete_confirm") == "yes":
            if not self.readonly_table:
                querysets.delete()
            return redirect("/my_admin/%s/%s/" % (app_name, table_name))
        selected_ids = ','.join([str(i.id) for i in querysets])
        return render(request, "my_admin/table_obj_delete.html", {"obj": querysets,
                                                                 "admin_class": self,
                                                                 "app_name": app_name,
                                                                 "table_name": table_name,
                                                                 "selected_ids": selected_ids,
                                                                 "action": request._admin_action,
                                                                 "errors": errors,
                                                                 })

    def default_form_validation(self):
        '''用户可以在此进行自定义的表单验证，相当于django form的clean方法'''
        pass

class CustomerAdmin(BaseAdmin):
    list_display = ['id', 'qq', 'name', 'source', 'consultant', 'consult_course', 'date', 'status','enroll']
    list_filters = ['source', 'consultant', 'consult_course', 'status', 'date']
    search_fields = ('qq', 'name', 'source', 'consultant__name')
    list_per_page = 3
    ordering = 'id'
    filter_horizontal = ('tags',)
    readonly_fields = ['qq', 'consultant','tags']
    # readonly_table = True

    # 自定义字段
    def enroll(self):
        # print("enroll", self.instance)
        if self.instance.status == 0:
            link_name = "报名新课程"
        else:
            link_name = "报名"
        return '''<a href="/sales/customer/%s/enrollment/" > %s</a>''' % (self.instance.id, link_name)
    enroll.display_name = "报名链接"



    actions = ["delete_selected_objs", "test"]
    # action
    def test(self, request, querysets):
        print("in test", )
        return redirect("/my_admin/")
    test.display_name = "测试动作"


    def default_form_validation(self):
        # print("-----customer validation ",self,'f43f43f43f34f43g')
        # print("----instance:",self.instance,'dj9jd94j39jt')
        consult_content = self.cleaned_data.get("content", '')
        if len(consult_content) < 15:
            return self.ValidationError(
                ('Field %(field)s 咨询内容记录不能少于15个字符'),
                code='invalid',
                params={'field': "content", },
            )

    def clean_name(self):
        print("name clean validation:", self.cleaned_data["name"])
        if not self.cleaned_data["name"]:
            self.add_error('name', "cannot be null")
        else:
            return self.cleaned_data['name']  # 切记return


class CustomerFollowUpAdmin(BaseAdmin):
    list_display = ('customer', 'consultant', 'date')
    list_per_page = 8


class UserProfileAdmin(BaseAdmin):
    list_display = ['email','name']
    readonly_fields = ['password',]
    modelform_exclude_fields = ["last_login",]
    filter_horizontal = ["user_permissions","groups"]


class StudyRecordAdmin(BaseAdmin):
    list_display = ['student','course_record','attendance','score','date']
    list_filters = ['course_record','score','attendance','course_record__from_class','student']

def register(real_model, admin_class):
    app_name = real_model._meta.app_label
    if app_name not in enable_admins:
        enable_admins[app_name] = {}

    admin_class.real_model = real_model
    model_name = real_model._meta.model_name
    enable_admins[app_name][model_name] = admin_class



register(models.Customer,CustomerAdmin)
register(models.CustomerFollowUp,CustomerFollowUpAdmin)
register(models.StudyRecord,StudyRecordAdmin)

register(models.UserProfile,UserProfileAdmin)