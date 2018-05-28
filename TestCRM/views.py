from django.shortcuts import render,redirect

from django.contrib.auth import login,authenticate,logout

from django.contrib.auth.decorators import login_required

# Create your views here.
from crm import models


def acc_login(request):
    errors = {}
    if request.method == 'POST':
        _email = request.POST.get('email')
        _password = request.POST.get('password')
        user = authenticate(username = _email, password = _password)

        if user:
            login(request,user)
            return redirect('/')

        else:
            errors['error'] = "Wrong username or password!"

    return render(request,'login.html',{'errors':errors})

def acc_logout(request):
    logout(request)
    return redirect("/account/login/")

@login_required(login_url='/account/login/')
def index(request):
    return render(request,'index.html')