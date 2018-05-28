
from django import template
register = template.Library()

@register.simple_tag
def render_enroll_contract(enroll_obj):
    return enroll_obj.enrolled_class.contract.template.format(course_name=enroll_obj.enrolled_class, stu_name=enroll_obj.customer.qq)