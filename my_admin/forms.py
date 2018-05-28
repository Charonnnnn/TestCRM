from django.utils.translation import ugettext as _
from django.forms import ValidationError

from django.forms import ModelForm

'''
class CustomerModelForm(ModelForm):
    class Meta:
        model =  models.Customer
        fields = "__all__"
'''
# 通过type生成类!!!!    '''动态生成'''
# class_obj = type('类名',(当前类的基类,),{'类成员':类成员})


def create_model_form(request, admin_class):
    '''动态生成MODEL FORM'''
    # __new__方法的调用是发生在__init__之前
    # 这是为了disable在add页面不影响添加
    def __new__(cls, *args, **kwargs):
        # print("base fields",cls.base_fields)
        for field_name,field_obj in cls.base_fields.items():
            # print(field_name,dir(field_obj))
            field_obj.widget.attrs['class'] = 'form-control'
            # field_obj.widget.attrs['maxlength'] = getattr(field_obj,'max_length' ) if hasattr(field_obj,'max_length') else ""

            if not hasattr(admin_class,"is_add_form"):  # 代表这是添加form,不需要disabled
                if field_name in admin_class.readonly_fields:
                    field_obj.widget.attrs['disabled'] = 'disabled'

            if hasattr(admin_class, "clean_%s" % field_name):
                field_clean_func = getattr(admin_class, "clean_%s" % field_name)
                setattr(cls, "clean_%s" % field_name, field_clean_func)

        return ModelForm.__new__(cls)

    def default_clean(self):
        '''给所有的form默认加一个clean验证'''
        print("1.running default clean", admin_class)
        print("2.running default clean", admin_class.readonly_fields)
        print("3.obj instance", self.instance)

        error_list = []
        if self.instance.id:  # 这是个修改的表单
            for field in admin_class.readonly_fields:
                print('*******!!!!!: ',field)
                field_val = getattr(self.instance, field)  # val in db
                if hasattr(field_val, "select_related"):  # m2m
                    m2m_objs = getattr(field_val, "select_related")().select_related()
                    m2m_vals = [i[0] for i in m2m_objs.values_list('id')]
                    set_m2m_vals = set(m2m_vals)
                    set_m2m_vals_from_frontend = set([i.id for i in self.cleaned_data.get(field)])
                    print("m2m", m2m_vals, set_m2m_vals_from_frontend)
                    if set_m2m_vals != set_m2m_vals_from_frontend:
                        # error_list.append(ValidationError(
                        #     _('Field %(field)s is readonly'),
                        #     code='invalid',
                        #     params={'field': field},
                        # ))
                        self.add_error(field, "readonly field")
                    continue

                field_val_from_frontend = self.cleaned_data.get(field)
                if field_val != field_val_from_frontend:
                    error_list.append(ValidationError(
                        _('Field %(field)s is readonly,data should be %(val)s'),
                        code='invalid',
                        params={'field': field, 'val': field_val},
                    ))

        # readonly_table check
        if admin_class.readonly_table:
            raise ValidationError(
                _('Table is readonly,cannot be modified or added'),
                code='invalid'
            )

        # invoke user's cutomized form validation
        self.ValidationError = ValidationError
        response = admin_class.default_form_validation(self)
        if response:
            error_list.append(response)

        if error_list:
            raise ValidationError(error_list)

    class Meta:
        model = admin_class.real_model
        fields = "__all__"
        exclude = admin_class.modelform_exclude_fields

    attr = {'Meta':Meta}
    # class_obj = type('类名',(当前类的基类,),{'类成员':类成员})
    model_form_class = type('DynamicModelForm',(ModelForm,),attr)
    setattr(model_form_class,'__new__',__new__)
    setattr(model_form_class,'clean',default_clean)

    return model_form_class