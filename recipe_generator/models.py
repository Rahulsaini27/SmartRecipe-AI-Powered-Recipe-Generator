from django.db import models
from django.contrib.auth.models import User

class Recipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    title = models.CharField(max_length=255) 
    ingredients = models.JSONField()  
    instructions = models.JSONField() 
    nutrition = models.JSONField()  
    created_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f"Recipe: {self.title} by {self.user.username}"
