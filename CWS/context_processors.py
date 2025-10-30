def add_session_variables(request):
    return {
        'user_id': request.session.get('user_id', ''),
        'fullName': request.session.get('fullName', ''),
        'userName': request.session.get('userName', ''),
        'token': request.session.get('token', ''),
    }
