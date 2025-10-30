from django.shortcuts import render

class CustomErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Si el DEBUG está activado, interceptamos los errores 404 y 500
        if response.status_code == 404:
            return render(request, 'handlers/404.html', status=404)
        """ if response.status_code == 500:
            return render(request, 'handlers/500.html', status=500) """
        return response
