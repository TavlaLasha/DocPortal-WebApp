from genericpath import exists
import json
from logging import fatal
from django.http.response import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout
)
from .models import User_Docs, File_Types
from  .forms import UserLoginForm, UserRegisterForm, DocForm
from django.db import transaction

from docx2pdf import convert
from pdf2docx import parse
import os, shutil
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files import File
from urllib.parse import unquote
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render

# from DocPortal.DocPortalApp import models

@csrf_exempt
def index(request):
    if request.method == 'POST':
        form = DocForm(request.POST, request.FILES)
        context={}
        if form.is_valid():
            uploaded_file = request.FILES['file']
            
            path = default_storage.save('to_be_converted_docs/'+uploaded_file.name, ContentFile(uploaded_file.read()))
            tmp_file = os.path.join(settings.MEDIA_ROOT, path)

            fbasename = os.path.splitext(os.path.basename(tmp_file))[0]

            outFilePath = ''

            if tmp_file.endswith('.docx'):
                outFilePath = os.path.join(settings.MEDIA_ROOT, 'converted_docs/' + fbasename + '.pdf')
                convert(tmp_file, outFilePath)
            elif tmp_file.endswith('.pdf'):
                outFilePath = os.path.join(settings.MEDIA_ROOT, 'converted_docs/' + fbasename + '.docx')
                parse(tmp_file, outFilePath)
            
            if outFilePath != '':
                supportedTypes = File_Types.objects.values_list('name', flat=True).distinct()[::1]
                fileType = File_Types.objects.filter(name = list(filter(outFilePath.endswith, supportedTypes))[0]).get()
                
                
                context['fileName'] = fbasename+'.'+fileType.name
            
            return JsonResponse(context)
    else:
        form = DocForm()
    return render(request, 'index.html', {'form': form})


def converted(request, doc):
    context={}
    if request.method == 'GET':
        if (doc != '') and (exists(os.path.join(settings.MEDIA_ROOT, 'converted_docs', doc))):
            f = default_storage.open(os.path.join('converted_docs', doc), 'r')
            context['fileUrl'] = os.path.join('/media/converted_docs/', doc)
            context['fileType'] = os.path.splitext(f.name)[1]
            context['fileName'] = doc
            context['fileSize'] = int(f.size/1024)
            # context['file'] = 
        
    return render(request, 'converted.html', context)

@login_required
def profile(request):
    uploaded = False
    deletedFile = ''
    if request.method == 'POST':
        if request.POST.get("fileName", False) and (exists(os.path.join(settings.MEDIA_ROOT, 'converted_docs', request.POST.get("fileName", False)))):
            doc = request.POST.get("fileName", False)
            os.replace(os.path.join(settings.MEDIA_ROOT,'converted_docs', doc), os.path.join(settings.MEDIA_ROOT,'docs', doc))
            f = default_storage.open(os.path.join(settings.MEDIA_ROOT,'docs', doc), 'rb')
            converted = File(f)

            if not User_Docs.objects.filter(file = os.path.join('docs', doc)).exists():
                model=User_Docs()
                model.user = request.user
                model.file = 'docs/'+ doc
                model.fileName = doc
                supportedTypes = File_Types.objects.values_list('name', flat=True).distinct()[::1]
                model.fileType = File_Types.objects.filter(name = list(filter(converted.name.endswith, supportedTypes))[0]).get()
                model.fileSize = converted.size/1024
                model.save()
            uploaded = True
        elif request.POST.get("fileUrl", False):
            dbDoc = unquote(request.POST.get("fileUrl", False).replace('/media/',''))
            try:
                print(dbDoc)
                foundDoc = User_Docs.objects.get(file=dbDoc)
                
                foundDoc.delete()

                doc = os.path.join(settings.MEDIA_ROOT,'docs', dbDoc.replace('docs/','', 1))
                os.remove(doc)
                deletedFile = dbDoc.replace('docs/','', 1)
            except User_Docs.DoesNotExist:
                pass
        else:
            form = DocForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = form.cleaned_data['file']
                saveDoc(request, uploaded_file)
                uploaded = True

    docs_list = User_Docs.objects.filter(user=request.user)
    paginator = Paginator(docs_list, 8) # Show 8 contacts per page.

    page_number = request.GET.get('page', 1)
    try:
        docs = paginator.page(page_number)
    except PageNotAnInteger:
        docs = paginator.page(1)
    except EmptyPage:
        docs = paginator.page(paginator.num_pages)
    return render(request, 'profile.html', {'docs':docs, 'uploaded':uploaded, 'deletedFile':deletedFile})

def delete(request, doc):
    if request.method == 'DELETE' and doc != '':
        clear_temp_files(doc)
    else:
        return HttpResponse(status=400)
    return HttpResponse(status=200)

def contact(request):
    return render(request, 'contact.html')

def terms(request):
    return render(request, 'termsconditions.html')


def login_view(request):
    next = request.GET.get('next')
    form = UserLoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        login(request, user)
        if next:
            return redirect(next)
        return redirect('/')
    context = {
        'form': form,
    }
    return render(request, 'auth/login.html', context)

def register_view(request):
    next = request.GET.get('next')
    form = UserRegisterForm(request.POST or None)
    
    if form.is_valid():
        user = form.save(commit=False)
        password = form.cleaned_data.get('password')
        user.set_password(password)
        user.save()

        new_user = authenticate(username=user.username, password=password)
        login(request, new_user)
        if next:
            return redirect(next)
        return redirect('/')
    context = {
        'form': form,
    }
    return render(request, 'auth/register.html', context)

def logout_view(request):
    logout(request)
    return redirect('/')

@login_required
def saveDoc(request, uploaded_file):
    model=User_Docs()
    model.user = request.user
    model.file = uploaded_file
    model.fileName = uploaded_file.name
    supportedTypes = File_Types.objects.values_list('name', flat=True).distinct()[::1]
    model.fileType = File_Types.objects.filter(name = list(filter(uploaded_file.name.endswith, supportedTypes))[0]).get()
    model.fileSize = uploaded_file.size/1024
    model.save()

def clear_temp_files(file=''):
    convertedFiles = os.path.join(settings.MEDIA_ROOT, 'converted_docs')
    tobeFiles = os.path.join(settings.MEDIA_ROOT, 'to_be_converted_docs')

    if file=='':
        for filename in os.listdir(convertedFiles):
            file_path = os.path.join(convertedFiles, filename)
            clear_file(file_path)
    else:
        if os.path.exists(os.path.join(convertedFiles, file)):
            os.remove(os.path.join(convertedFiles, file))

    for filename in os.listdir(tobeFiles):
        file_path = os.path.join(tobeFiles, filename)
        clear_file(file_path)
        

def clear_file(file_path):
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))