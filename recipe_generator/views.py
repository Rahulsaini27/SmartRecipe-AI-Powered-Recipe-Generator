import re
import nltk
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from nltk.corpus import stopwords
from dotenv import load_dotenv 
from django.http import JsonResponse
import json
# Recipe generation function
import os
import json
import google.generativeai as genai
from django.core.paginator import Paginator, Page

# Check all available attributes and methods of the module
print(dir(genai))
# Ensure stopwords are downloaded
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

from .models import Recipe  # Assuming the Recipe model exists
from .forms import SignUpForm, LoginForm


# Initialize the Gemini model with the correct method
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))  # Use the environment variable for security

# Preprocessing function for text cleaning
def clean_text(text):
    text = text.lower()  # Lowercase the text
    text = re.sub(r"http\S+|www\S+|https\S+", '', text, flags=re.MULTILINE)  # Remove URLs
    text = re.sub(r'\@w+|\#','', text)  # Remove mentions and hashtags
    text = re.sub(r'[^A-Za-z\s]', '', text)  # Remove punctuation
    text = ' '.join([word for word in text.split() if word not in stop_words])  # Remove stopwords
    return text

# Home view
def home(request):
    return render(request, 'home.html')

# Signup view
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Signup successful. Please log in.')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

# Login view
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request,
                                username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect('generate-recipes')
            else:
                messages.error(request, 'Invalid credentials')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

# Logout view
def user_logout(request):
    logout(request)
    return redirect('home')

def recipehistory(request):
    # Fetch the recipes created by the logged-in user, ordered by creation date
    records = Recipe.objects.filter(user=request.user).order_by('-created_at')
    
    # If you want pagination, you can use Django's Paginator
    from django.core.paginator import Paginator
    
    paginator = Paginator(records, 10)  # Show 10 recipes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Render the 'recipehistory.html' template with the recipes passed as context
    return render(request, 'recipehistory.html', {'page_obj': page_obj})

# Ensure stopwords are downloaded
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# Load environment variables
load_dotenv()

# Initialize the Gemini model with the correct method
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))  # Use the environment variable for security

# Preprocessing function for text cleaning
def clean_text(text):
    text = text.lower()  # Lowercase the text
    text = re.sub(r"http\S+|www\S+|https\S+", '', text, flags=re.MULTILINE)  # Remove URLs
    text = re.sub(r'\@w+|\#','', text)  # Remove mentions and hashtags
    text = re.sub(r'[^A-Za-z\s]', '', text)  # Remove punctuation
    text = ' '.join([word for word in text.split() if word not in stop_words])  # Remove stopwords
    return text

# Assuming the genai module is properly imported

@csrf_exempt
@login_required  # Only allow logged-in users to generate recipes
def generate_recipes(request):
    if request.method == "GET":
        return render(request, 'recipe.html')

    elif request.method == "POST":
        try:
            print("Starting custom recipe generation...")

            data = json.loads(request.body)
            ingredients = data.get('items', [])

            if len(ingredients) < 4:
                return JsonResponse({"error": "Please provide at least 4 ingredients."}, status=400)

            model = genai.GenerativeModel('gemini-1.5-flash')

            user_prompt = f"""
            Generate a recipe with the following ingredients: {', '.join(ingredients)}.
            The recipe should include:
            - A creative and engaging title.
            - A list of ingredients.
            - Step-by-step instructions on how to prepare the dish.
            - Nutritional information (calories, protein, carbs, fat).
            """

            response = model.generate_content(user_prompt)

            response_text = response.text
            print(f"Response Text: {response_text}")

            if not response_text:
                return JsonResponse({"error": "Empty response from Gemini API. Please try again."}, status=500)

            try:
                # Parse Gemini response
                title_start = response_text.find('## ') + 3
                title_end = response_text.find('\n', title_start)
                title = response_text[title_start:title_end].strip()

                ingredients_start = response_text.find('**Ingredients:**') + len('**Ingredients:**')
                ingredients_end = response_text.find('**Instructions:**')
                ingredients_text = response_text[ingredients_start:ingredients_end].strip()
                ingredients_list = [line.strip('* ').strip() for line in ingredients_text.split('\n') if line.strip()]

                instructions_start = response_text.find('**Instructions:**') + len('**Instructions:**')
                instructions_end = response_text.find('**Nutritional Information:**')
                instructions_text = response_text[instructions_start:instructions_end].strip()
                instructions_list = [line.strip() for line in instructions_text.split('\n') if line.strip()]

                nutrition_start = response_text.find('**Nutritional Information (per serving):**') + len('**Nutritional Information (per serving):**')
                nutrition_text = response_text[nutrition_start:].strip()
                nutrition_lines = nutrition_text.split('\n')
                nutrition = {}
                for line in nutrition_lines:
                    if line.startswith('* **Calories:**'):
                        nutrition["calories"] = line.split(':')[1].strip()
                    elif line.startswith('* **Protein:**'):
                        nutrition["protein"] = line.split(':')[1].strip()
                    elif line.startswith('* **Carbs:**'):
                        nutrition["carbohydrates"] = line.split(':')[1].strip()
                    elif line.startswith('* **Fat:**'):
                        nutrition["fat"] = line.split(':')[1].strip()

                # Save to database (including the user!)
                recipe = Recipe.objects.create(
                    user=request.user,
                    title=title,
                    ingredients=ingredients_list,
                    instructions=instructions_list,
                    nutrition=nutrition
                )

                print(f"Recipe Saved: {recipe}")

                output = {
                    "title": title,
                    "ingredients": ingredients_list,
                    "instructions": instructions_list,
                    "nutrition": nutrition
                }

                return JsonResponse(output)

            except Exception as e:
                print(f"Error parsing the response text: {str(e)}")
                return JsonResponse({"error": "Error parsing the response text from Gemini API."}, status=500)

        except Exception as e:
            print(f"Exception: {str(e)}")
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)