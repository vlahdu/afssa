from django import forms 
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from core.models import MediaUpload, Rating

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Enter your username',
        'class':'w-full py-4 px-6 dark:text-black rounded-xl'
    }))   
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Enter your password',
        'class':'w-full py-4 px-6 dark:text-black rounded-xl'
    }))
    
class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username','email','password1','password2')

    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Enter your username',
        'class':'w-full py-4 px-6   dark:text-black rounded-xl'
    }))
    email = forms.CharField(widget=forms.EmailInput(attrs={
        'placeholder':'Enter your email',
        'class':'w-full py-4 px-6   dark:text-black rounded-xl'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Enter your password',
        'class':'w-full py-4 px-6  dark:text-black  rounded-xl'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Check your password',
        'class':'w-full py-4 px-6   dark:text-black rounded-xl'
    }))

from django import forms
from django.core.exceptions import ValidationError
from .models import MediaUpload, Rating

class MediaUploadForm(forms.ModelForm):
    class Meta:
        model = MediaUpload
        fields = ['category', 'audio', 'video', 'image']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control', 'style': 'color: black;'}),
        }

    def __init__(self, *args, **kwargs):
        super(MediaUploadForm, self).__init__(*args, **kwargs)
        self.fields['category'].initial = 'wav2lip'

    def clean(self):
        cleaned_data = super().clean()
        audio = cleaned_data.get('audio')
        video = cleaned_data.get('video')
        image = cleaned_data.get('image')
        category = cleaned_data.get('category')

        if category == 'makeittalk' and not image:
            raise ValidationError('You must upload an image for MakeItTalk.')

        if category != 'makeittalk' and not video:
            raise ValidationError('You must upload a video for Wav2Lip and SadTalker.')

        if audio:
            valid_audio_extensions = ['.wav', '.mp3', '.ogg', '.flac']
            if not any(audio.name.lower().endswith(ext) for ext in valid_audio_extensions):
                raise ValidationError('Invalid audio file extension. Allowed extensions are: .wav, .mp3, .ogg, .flac')

        return cleaned_data


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['facial_inconsistencies', 'glitches_or_artifacts', 'background_quality', 'lip_sync_accuracy']
        widgets = {
            'facial_inconsistencies': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '5', 'style': 'color: #000000; font-size: 1.25rem;'}),
            'glitches_or_artifacts': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '5', 'style': 'color: #000000; font-size: 1.25rem;'}),
            'background_quality': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '5', 'style': 'color: #000000; font-size: 1.25rem;'}),
            'lip_sync_accuracy': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '5', 'style': 'color: #000000; font-size: 1.25rem;'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        facial_inconsistencies = cleaned_data.get('facial_inconsistencies')
        glitches_or_artifacts = cleaned_data.get('glitches_or_artifacts')
        background_quality = cleaned_data.get('background_quality')
        lip_sync_accuracy = cleaned_data.get('lip_sync_accuracy')

        if not (1 <= facial_inconsistencies <= 5):
            raise forms.ValidationError("Facial inconsistencies rating must be between 1 and 5.")
        if not (1 <= glitches_or_artifacts <= 5):
            raise forms.ValidationError("Glitches or artifacts rating must be between 1 and 5.")
        if not (1 <= background_quality <= 5):
            raise forms.ValidationError("Background quality rating must be between 1 and 5.")
        if not (1 <= lip_sync_accuracy <= 5):
            raise forms.ValidationError("Lip sync accuracy rating must be between 1 and 5.")

        overall_score = (facial_inconsistencies + glitches_or_artifacts + background_quality + lip_sync_accuracy) / 4
        cleaned_data['overall_score'] = overall_score

        return cleaned_data