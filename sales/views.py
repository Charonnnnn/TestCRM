from django.shortcuts import render,redirect,HttpResponse
from crm import models
from my_admin.my_admin import enable_admins
from sales import forms
import random,string,os
from django.core.cache import cache
from TestCRM import settings
from django.db import IntegrityError

# Create your views here.


def sales_index(request):
    return render(request,'sales/index.html')

def customer_list(request):
    # 其实调用这句即可, 因为在index.html侧边栏的超链接不同menu类型不同连接
    # return render(request,'index.html')
    return render(request,'sales/customer_list.html')

def enrollment(request,customer_id):

    customer_obj = models.Customer.objects.get(id=customer_id)
    msgs = {}
    if request.method == "POST":
        enroll_form = forms.EnrollmentForm(request.POST)
        if enroll_form.is_valid():
            msg = '''请将此链接发送给客户进行填写:
                http://localhost:8000/sales/customer/registration/{enroll_obj_id}/{random_str}/'''
            try:
                enroll_form.cleaned_data["customer"] = customer_obj
                enroll_obj = models.Enrollment.objects.create(**enroll_form.cleaned_data)
                msgs["msg"] = msg.format(enroll_obj_id=enroll_obj.id)
            # 若是已存在
            except IntegrityError as e :
                enroll_obj = models.Enrollment.objects.get(customer_id=customer_obj.id,
                                                           enrolled_class_id=enroll_form.cleaned_data["enrolled_class"].id)

                if enroll_obj.contract_agreed: #学生已经同意了
                    return redirect("/sales/contract_review/%s/"%enroll_obj.id)

                enroll_form.add_error("__all__","该用户的此条报名信息已存在，不能重复创建")

                random_str = "".join(random.sample(string.ascii_lowercase+string.digits, 8))
                cache.set(enroll_obj.id, random_str,3000)
                msgs["msg"] = msg.format(enroll_obj_id=enroll_obj.id,random_str=random_str)

    else:
        enroll_form = forms.EnrollmentForm()

    return render(request,"sales/enrollment.html",{"enroll_form":enroll_form,
                                                   "customer_obj":customer_obj,
                                                   "msgs":msgs})

def stu_registration(request,enroll_id,random_str):
    if cache.get(enroll_id) == random_str:
        enroll_obj = models.Enrollment.objects.get(id=enroll_id)

        if request.method == "POST":
            if request.is_ajax():   # 图片上传 (ajax)
                # print("ajax post, ", request.FILES)
                enroll_data_dir = "%s/%s" %(settings.ENROLLED_DATA,enroll_id)
                if not os.path.exists(enroll_data_dir):
                    os.makedirs(enroll_data_dir,exist_ok=True)

                for k,file_obj in request.FILES.items():
                    with open("%s/%s"%(enroll_data_dir, file_obj.name), "wb") as f:
                        for chunk in file_obj.chunks():
                            f.write(chunk)
                return HttpResponse("success")

            customer_form = forms.CustomerForm(request.POST,instance=enroll_obj.customer)  # 修改
            if customer_form.is_valid():
                customer_form.save()
                enroll_obj.contract_agreed = True
                enroll_obj.save()
                return render(request,"sales/stu_registration.html",{"status":1})
        else: # GET
            if enroll_obj.contract_agreed == True:
                status =  1
            else:
                status =  0
            customer_form = forms.CustomerForm(instance=enroll_obj.customer)

            return  render(request,"sales/stu_registration.html",
                       {"customer_form":customer_form,
                        "enroll_obj":enroll_obj,
                        "status":status})
    else:
        return HttpResponse("链接过期")

def contract_review(request,enroll_id):
    enroll_obj = models.Enrollment.objects.get(id=enroll_id)
    enroll_form = forms.EnrollmentForm(instance=enroll_obj)
    customer_form = forms.CustomerForm(instance=enroll_obj.customer)
    return render(request, 'sales/contract_review.html', {
                                                "enroll_obj":enroll_obj,
                                                "enroll_form":enroll_form,'customer_form':customer_form})

def enrollment_rejection(request,enroll_id):

    enroll_obj = models.Enrollment.objects.get(id=enroll_id)
    enroll_obj.contract_agreed = False
    enroll_obj.save()

    return  redirect("/crm/customer/%s/enrollment/" %enroll_obj.customer.id)

def payment(request,enroll_id):
    enroll_obj = models.Enrollment.objects.get(id=enroll_id)
    errors = []
    if request.method == "POST":
        payment_amount = request.POST.get("amount")
        if payment_amount:
            payment_amount = int(payment_amount)

            if payment_amount < 500:
                errors.append("缴费金额不得低于500元")
            else:
                payment_obj = models.Payment.objects.create(
                    customer= enroll_obj.customer,
                    course = enroll_obj.enrolled_class.course,
                    amount = payment_amount,
                    consultant = enroll_obj.consultant
                )
                enroll_obj.contract_approved = True
                enroll_obj.save()


                enroll_obj.customer.status = 0
                enroll_obj.customer.save()
                return redirect("/my_admin/crm/customer/")
        else:
            errors.append("缴费金额不得低于500元")
    # print("errors",errors)
    return render(request,"sales/payment.html",{'enroll_obj':enroll_obj,'errors':errors})