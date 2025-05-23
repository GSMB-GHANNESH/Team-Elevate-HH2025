from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.middleware.csrf import get_token
from django.views.generic import TemplateView
from .models import CustomUser, Community, CommunityMembership
import logging
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import requests
import os

logger = logging.getLogger(__name__)

def login_view(request):
    """Display the login page."""
    if request.user.is_authenticated:
        return redirect('companions:home')
    return render(request, 'html/login.html')

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Handle login API request."""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({
                'success': False,
                'error': 'Email and password are required'
            }, status=400)

        # Use authenticate with email parameter
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'user': {
                        'email': user.email,
                        'name': user.name,
                        'id': user.id
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Account is disabled'
                }, status=401)
            
        return JsonResponse({
            'success': False,
            'error': 'Invalid email or password'
        }, status=401)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred during login'
        }, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Handle user registration."""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
            
        # Validate required fields
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)
            
        if CustomUser.objects.filter(email=data.get('email')).exists():
            return JsonResponse({
                'success': False,
                'error': 'Email already registered'
            }, status=400)
            
        user = CustomUser.objects.create_user(
            email=data.get('email'),
            password=data.get('password'),
            name=data.get('name'),
            birth_date=data.get('birth_date', None),
            phone=data.get('phone', ''),
            city=data.get('city', '')
        )
        
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'user': {
                'email': user.email,
                'name': user.name,
                'id': user.id
            }
        })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format'
        }, status=400)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@ensure_csrf_cookie
@require_http_methods(["POST"])
@login_required
def logout_view(request):
    """Log out the user."""
    logout(request)
    return JsonResponse({
        'success': True,
        'redirect': '/login/'
    })

@login_required
def home_view(request):
    """Display the home page."""
    return render(request, 'html/home.html')

# --- Profile Views ---


@login_required
def profile_view(request):
    """Render the user profile page."""
    return render(request, 'html/profile.html')

@login_required
@require_POST
def profile_update_view(request):
    """Handle the profile update form submission."""
    user = request.user
    # Example: update first and last name
    user.first_name = request.POST.get('first_name', user.first_name)
    user.last_name = request.POST.get('last_name', user.last_name)
    user.save()
    return redirect('companions:profile')

@login_required
def profile_api(request):
    """API endpoint for profile data."""
    # Return profile data as JSON
    data = {
        'username': request.user.username,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
    }
    return JsonResponse(data)

# --- Other Views ---


@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """
    Returns CSRF token for the frontend to use in subsequent requests
    """
    return JsonResponse({'csrfToken': get_token(request)})

@ensure_csrf_cookie
def react_app_view(request):
    """Serve the React application."""
    return render(request, 'html/react_app.html')

def community_view(request):
    """Display the community page."""
    return HttpResponse("This is the community page.")

@login_required
def dashboard_view(request):
    """Render the dashboard page."""
    return render(request, 'html/dashboard.html')

def settings_view(request):
    """Render the settings page."""
    return HttpResponse("This is the settings page.")

@require_http_methods(["GET"])
def check_auth(request):
    """Return JSON indicating whether the user is authenticated."""
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'email': getattr(request.user, 'email', ''),
            'name': request.user.first_name or request.user.username,
            'id': request.user.id
        })
    return JsonResponse({'authenticated': False})

@require_http_methods(["GET"])
def test_view(request):
    if request.user.is_authenticated:
        return JsonResponse({"message": "This is a protected endpoint"})
    else:
        return JsonResponse({"error": "Authentication required"}, status=401)

@login_required
def profile_view(request):
    return render(request, 'html/profile.html')


@login_required
def community_list(request):
    if request.method == 'GET':
        communities = Community.objects.all()
        return render(request, 'html/community_list.html', {'communities': communities})
    return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required
def join_community(request, community_id):
    if request.method == 'POST':
        try:
            community = Community.objects.get(id=community_id)
            membership, created = CommunityMembership.objects.get_or_create(user=request.user, community=community)
            if created:
                return JsonResponse({"message": "Joined community successfully"})
            else:
                return JsonResponse({"message": "Already a member of this community"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Community not found"}, status=404)
    return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required
def create_community(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if not name or not description:
            return JsonResponse({"error": "Name and description are required"}, status=400)
        community = Community.objects.create(name=name, description=description, created_by=request.user)
        CommunityMembership.objects.create(user=request.user, community=community)
        return redirect('community_list')
    return render(request, 'html/create_community.html')

@login_required
def community_detail(request, community_id):
    try:
        community = Community.objects.get(id=community_id)
        if request.method == 'GET':
            return render(request, 'html/community_detail.html', {'community': community})
        elif request.method == 'POST':
            message = request.POST.get('message')
            if message:
                # Save the message to the community's chat
                # Assuming you have a Message model
                # Message.objects.create(user=request.user, community=community, content=message)
                pass
            return redirect('community_detail', community_id=community_id)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "Community not found"}, status=404)

@csrf_exempt
def TextGenerationView(request):
    if request.method == "POST":
        try:
            # Parse JSON data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON"}, status=400)
                
            prompt = data.get("prompt", "")
            language = data.get("language", "english")

            # Debug print
            print(f"Received request - Prompt: {prompt}, Language: {language}")

            # Call Groq API
            headers = {
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": f"You are a helpful assistant who replies in {language}."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )

            # Debug print
            print(f"Groq API response: {response.status_code}")

            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return JsonResponse({"response": content})
            else:
                return JsonResponse(
                    {"error": f"Groq API error: {response.text}"},
                    status=response.status_code
                )

        except Exception as e:
            print(f"Server error: {str(e)}")  # Debug print
            return JsonResponse(
                {"error": f"Server error: {str(e)}"},
                status=500
            )
    return JsonResponse({"error": "Method not allowed"}, status=405)
    
def homeView(request):
    return render(request, 'chatb.html')
    
class ReactAppView(TemplateView):
    template_name = 'html/react_app.html'