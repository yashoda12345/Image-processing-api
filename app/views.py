from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from .models import User
from PIL import Image
import jwt, json, pytesseract, cv2, re, numpy


pytesseract.pytesseract.tesseract_cmd = r'app/utils/Tesseract-OCR/tesseract.exe'


'''This function will return the data in the pan card in the form of dictionary.
Based on some patterns in the text it collects the data '''
def pan_data_extraction(pan_list):
    try:
        d = dict()
        # creating pattern for DOB
        dob_pattern = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')
        for i in range(len(pan_list)):
            if 'Permanent Account Number Card' == pan_list[i]:
                d['permanent_account_number'] = pan_list[i + 1]
            if 'father\'s' in pan_list[i].lower() and 'name' in pan_list[i].lower():
                d['father_name'] = pan_list[i + 1]
            elif 'name' in pan_list[i].lower():
                d['name'] = pan_list[i + 1]
            if dob_pattern.search(pan_list[i]):
                data_match = dob_pattern.search(pan_list[i])
                d['d_o_b'] = data_match.group(1)
        return d
    except Exception as e:
        return JsonResponse({'error': str(e)})



'''This function will return the data in the aadhar card in the form of dictionary.
Based on some patterns in the text it collects the data '''
def aadhar_data_extraction(aadhar_list):
    try:
        # Creating patterns to find number and DOB
        number_pattern = r'^[0-9]{4}\s[0-9]{4}\s[0-9]{4}$'
        dob_pattern = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')

        d = dict()
        for i in range(len(aadhar_list)):
            if re.match(number_pattern, aadhar_list[i]):
                d['aadhar_number'] = aadhar_list[i]
            if dob_pattern.search(aadhar_list[i]):
                date_match = dob_pattern.search(aadhar_list[i])
                d['d_o_b'] = date_match.group(1)
                d['name'] = aadhar_list[i - 1]
            if 'mal' in aadhar_list[i].lower() or 'male' in aadhar_list[i].lower():
                d['gender'] = 'Male'
            if 'female' in aadhar_list[i].lower() or 'fema' in aadhar_list[i].lower():
                d['gender'] = 'Female'
        return d
    except Exception as e:
        return JsonResponse({'error': str(e)})



'''This function will validate the type of file and size of the file'''
def is_file_valid(file_name, file_size):
    try:
        file_types = ['png', 'jpeg', 'jpg']
        if file_name.split('.')[-1].lower() in file_types and file_size < 2 * 1024 * 1024:
            return True
        else: return False
    except Exception as e:
        return JsonResponse({'error': str(e)})



''' This function will extract the text from the image using tesseract-OCR and remove unwanted data
and convert the data into a list 
'''
def image_text_extraction(image):
    try:
        gray_image = cv2.cvtColor(numpy.array(Image.open(image)), cv2.COLOR_BGR2GRAY)
        text_list = pytesseract.image_to_string(gray_image).split('\n')
        while '' in text_list:
            text_list.remove('')
        return text_list
    except Exception as e:
        return JsonResponse({'error': str(e)})


@api_view(['POST'])
def document_extraction(request):
    try:

        if request.method == 'POST':
            try:
                if 'pan' in request.data:
                    file_name = request.FILES['pan'].name
                    file_size = request.FILES['pan'].size
                    if request.FILES['pan'].read() and is_file_valid(file_name, file_size):
                        result = pan_data_extraction(image_text_extraction(request.FILES['pan'].file))
                        return JsonResponse({'result': result})
                    else:
                        return JsonResponse({'error': 'unsupported media type'}, status=415)

                elif 'aadhar' in request.data:
                    file_name = request.FILES['aadhar'].file
                    file_size = request.FILES['aadhar'].file
                    if request.FILES['aadhar'].read() and is_file_valid(file_name, file_size):
                        result = aadhar_data_extraction(image_text_extraction(request.FILES['aadhar'].file))
                        return JsonResponse({'result': result})
                    else:
                        return JsonResponse({'error': 'unsupported media type'}, status=415)
            except Exception as e:
                return JsonResponse({'error': str(e)})

    except Exception as e:
        return JsonResponse({'error': str(e)})

@api_view(['POST'])
def user_creation(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        hashed_password = make_password(password)
        user = User(username = username, password = hashed_password)
        user.save()
        return JsonResponse({'success':'record created successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)})

@api_view(['POST'])
def user_authentication(request):
    try:
        data = json.loads(request.body)
        entered_username = data.get('username')
        entered_password = data.get('password')
        try:
            user = User.objects.get(username = entered_username)
        except:
            return JsonResponse({'error':'Invalid Username/Password'})
        p = user.password
        if check_password(entered_password, user.password):
            payload = {'name': user.username}
            secret_key = settings.JWT_SECRET_KEY
            jwt_token = jwt.encode(payload, secret_key, algorithm='HS256')
            return JsonResponse({'token': jwt_token})
        else:
            return JsonResponse({'error': 'Invalid username/password'})
    except Exception as e:
        return JsonResponse({'error': str(e)})

