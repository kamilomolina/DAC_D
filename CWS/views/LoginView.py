from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connections
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime, timedelta
import requests
import pandas as pd
import time
import hashlib
import subprocess
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from django.urls import reverse

LOGIN_URL = 'http://3.230.160.184:81/CWS'
SECRET_KEY = 'a0a952043ced9096cf47e8405f23729d' 
EXPIRATION_MINUTES = 90

def login(request):
    request.session.flush()

    token = ''
    empresas = obtener_empresas()
    return render(request, 'login.html',  {'empresas': empresas})



def loginRequest(request):
    request.session.flush()

    token = ''
    
    php_script_path = './DAC/views/md5.php'

    username = request.POST.get('username')
    password = request.POST.get('password')
    empresa = request.POST.get('empresa')

    result = subprocess.run(['php', php_script_path, password], stdout=subprocess.PIPE)

    crypted_pass = result.stdout.decode('utf-8').strip()

    account = 0
    module = 0
    token = ''

    user_id = 480
    fullName = 'KAMILO ALEJANDRO MOLINA COREA'
    userName = 'KAMILO'
    account = 1

    section = 0

    try:
        with connections['global_nube'].cursor() as cursor:
            cursor.callproc("SDK_GET_USER_ACCESS", [username, crypted_pass])
            accountQuery = cursor.fetchall()
            
            if accountQuery:
                account = 1
                user_id = accountQuery[0][0]
                fullName = accountQuery[0][1]
                userName = accountQuery[0][2]

        with connections['global_nube'].cursor() as cursor:
            cursor.callproc("SDK_GET_USER_MODULE_ACCESS", [17, user_id])
            moduleQuery = cursor.fetchall()
            
            if moduleQuery:
                module = 1

                request.session.cycle_key()

                request.session['user_id'] = user_id
                request.session['fullName'] = fullName
                request.session['userName'] = userName
                request.session['empresa'] = empresa

                expiration = datetime.utcnow() + timedelta(minutes=EXPIRATION_MINUTES)
                token_payload = {
                    'user_id': user_id,
                    'username': userName,
                    'exp': expiration
                }
                token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')
                request.session['token'] = token.decode('utf-8') if isinstance(token, bytes) else token
                if isinstance(token, bytes):
                    token = token.decode('utf-8')

                request.session['token'] = token


        datos = {'save': 1, 'account': account, 'module': module, 'token': token, 'section': section}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)



def logoutRequest(request):
    request.session.flush()

    token = ''

    return HttpResponseRedirect(reverse('login'))



def modulos(request):
    user_id = request.session.get('user_id', '')
    username = request.session.get('userName', '')

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        return render(request, 'modulos.html')



def moduleRequest(request):
    user_id = request.POST.get('user_id')
    username = request.POST.get('username')
    modulo = request.POST.get('modulo')
    module =0
    
    try:
        with connections['global_nube'].cursor() as cursor:
            cursor.callproc("SDK_GET_USER_MODULE_ACCESS", [modulo, user_id])
            moduleQuery = cursor.fetchall()

            if moduleQuery:
                module = 1

        datos = {'save': 1, 'module': module}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)



def obtener_empresas():
    empresas_list = []
    try:
        with connections['global_nube'].cursor() as cursor:
            cursor.execute("CALL TH_GET_EMPRESAS()")
            empresas = cursor.fetchall()
            empresas_list = [{'id': empresa[1], 'nombre': empresa[0]} for empresa in empresas]

    except Exception as e:
        print(e)
    return empresas_list



def custom_404(request, exception=None):
    return render(request, 'handlers/404.html', status=404)