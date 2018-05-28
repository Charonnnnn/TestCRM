from django.shortcuts import render

# Create your views here.


def tea_index(request):
    return render(request,'teacher/index.html')