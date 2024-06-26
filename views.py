import os   
import subprocess
import shutil
from django.shortcuts import render, redirect, get_object_or_404   
from django.contrib.auth.decorators import login_required  
from django.db.models import Avg, Q, F  
from .models import MediaUpload, Rating 
from .forms import MediaUploadForm, RatingForm, SignupForm 
from django.contrib.auth import logout, login 
from django.conf import settings 

@login_required  
def generate_video(request):
    if request.method == 'POST':   
        form = MediaUploadForm(request.POST, request.FILES)  
        if form.is_valid():
            media = form.save(commit=False)  # Saving form data to media object without committing to DB

            # Setting creator of the media
            media.created_by = request.user

            # Handling specific cases based on media category
            if media.category == 'sadtalker' and 'video' in request.FILES:
                media.image = request.FILES['video']
                media.video = None

            media.save()   

            # Obtaining paths for uploaded files
            video_path = os.path.join(settings.MEDIA_ROOT, media.video.name) if media.video else None
            audio_path = os.path.join(settings.MEDIA_ROOT, media.audio.name) if media.audio else None
            image_path = os.path.join(settings.MEDIA_ROOT, media.image.name) if media.image else None

            original_dir = os.getcwd()  # Saving current working directory

            try:
                # Handling video generation based on category
                if media.category == 'wav2lip':
                    # Checking required paths for wav2lip
                    if not video_path or not audio_path:
                        raise ValueError("Video path and audio path must be provided for wav2lip.")

                    result_path = os.path.join('wav2lip', 'results', 'result_voice.mp4')

                    # Running subprocess command for wav2lip
                    command = [
                        'python', 'wav2lip/inference.py',
                        '--checkpoint_path', 'wav2lip/checkpoints/wav2lip_gan.pth',
                        '--face', video_path,
                        '--audio', audio_path,
                        '--outfile', result_path
                    ]
                    subprocess.run(command, check=True)  # Executing command and checking for errors

                    # Creating directory for user's generated videos
                    user_folder = os.path.join(settings.MEDIA_ROOT, 'generated_videos', request.user.username)
                    os.makedirs(user_folder, exist_ok=True)

                    # Copying generated video to user's directory
                    generated_video_name = f"generated_{media.id}_result_voice.mp4"
                    generated_video_media_path = os.path.join(user_folder, generated_video_name)
                    shutil.copy(result_path, generated_video_media_path)

                    # Updating media instance with generated video path
                    media.video = os.path.join('generated_videos', request.user.username, generated_video_name)
                    media.save()

                elif media.category == 'sadtalker':
                    # Checking required paths for sadtalker
                    if not audio_path or not image_path:
                        print("Audio or image path not found:")
                        print(f"audio_path: {audio_path}")
                        print(f"image_path: {image_path}")
                        raise ValueError("Audio path and image path must be provided for sadtalker.")

                    os.chdir('SadTalker-main')  # Changing directory to SadTalker's main directory

                    # Setting up command for sadtalker inference
                    command = f'''
                    source $(conda info --base)/etc/profile.d/conda.sh && \
                    conda activate sadtalker && \
                    python inference.py --driven_audio {audio_path} --source_image {image_path} --enhancer gfpgan && \
                    conda deactivate
                    '''
                    subprocess.run(command, shell=True, check=True, executable='/bin/bash')  # Running command

                    result_dir = os.path.join('results')
                    result_files = os.listdir(result_dir)
                    result_files.sort(key=lambda x: os.path.getmtime(os.path.join(result_dir, x)), reverse=True)
                    result_file = result_files[0] if result_files else None

                    if result_file:
                        result_path = os.path.join(result_dir, result_file)
                        
                        # Creating directory for user's generated videos
                        user_folder = os.path.join(settings.MEDIA_ROOT, 'generated_videos', request.user.username)
                        os.makedirs(user_folder, exist_ok=True)

                        # Copying generated video to user's directory
                        generated_video_name = f"generated_{media.id}_result_video.mp4"
                        generated_video_media_path = os.path.join(user_folder, generated_video_name)
                        shutil.copy(result_path, generated_video_media_path)

                        # Updating media instance with generated video path
                        media.video = os.path.join('generated_videos', request.user.username, generated_video_name)
                        media.save()

                    os.chdir(original_dir)  # Returning to original directory after operation

                elif media.category == 'makeittalk':
                    # Setting up paths for makeittalk
                    makeittalk_dir = os.path.join('MakeItTalk-main', 'examples')
                    audio_target_path = os.path.join(makeittalk_dir, os.path.basename(media.audio.name)) if media.audio else None
                    image_target_path = os.path.join(makeittalk_dir, os.path.basename(media.image.name)) if media.image else None

                    # Checking required paths for makeittalk
                    if not audio_target_path or not image_target_path:
                        raise ValueError("Audio path and image path must be provided for makeittalk.")
                    
                    # Copying uploaded files to makeittalk directory
                    if media.audio:
                        shutil.copy(media.audio.path, audio_target_path)
                    if media.image:
                        shutil.copy(media.image.path, image_target_path)

                    os.chdir('MakeItTalk-main')  # Changing directory to MakeItTalk's main directory

                    # Setting up command for makeittalk
                    command = [
                        'python', 'main_end2end.py',
                        '--jpg', os.path.basename(image_target_path)
                    ]
                    subprocess.run(command, check=True)  # Running command

                    result_dir = os.path.join('examples')
                    result_files = os.listdir(result_dir)
                    result_files.sort(key=lambda x: os.path.getmtime(os.path.join(result_dir, x)), reverse=True)
                    result_file = None

                    # Finding generated result file in examples folder
                    for file in result_files:
                        if file.startswith(os.path.splitext(os.path.basename(image_target_path))[0] + "_pred"):
                            result_file = file
                            break

                    if result_file:
                        result_path = os.path.join(result_dir, result_file)
                        
                        # Creating directory for user's generated videos
                        user_folder = os.path.join(settings.MEDIA_ROOT, 'generated_videos', request.user.username)
                        os.makedirs(user_folder, exist_ok=True)

                        # Copying generated video to user's directory
                        generated_video_name = f"generated_{media.id}_result_video.mp4"
                        generated_video_media_path = os.path.join(user_folder, generated_video_name)
                        shutil.copy(result_path, generated_video_media_path)

                        # Updating media instance with generated video path
                        media.video = os.path.join('generated_videos', request.user.username, generated_video_name)
                        media.save()

                    os.chdir(original_dir)  # Returning to original directory after operation

                    # Deleting unnecessary files in examples folder
                    for item in os.listdir(makeittalk_dir):
                        item_path = os.path.join(makeittalk_dir, item)
                        if os.path.isdir(item_path):
                            if item not in ['ckpt', 'dump']:
                                shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)

                # Removing temporary uploaded files
                if video_path and os.path.exists(video_path):
                    os.remove(video_path)
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
                if image_path and os.path.exists(image_path):
                    os.remove(image_path)

                return redirect('core:index') 

            except subprocess.CalledProcessError as e:
                print(f"Error during video generation: {e}")  
            except Exception as e:
                print(f"Unexpected error during video generation: {e}")   

    else:
        form = MediaUploadForm()  # Creating a blank form for GET requests

    return render(request, 'core/generate_video.html', {
        'form': form,   
    })


@login_required  
def toggle_visibility(request, video_id):
    video = get_object_or_404(MediaUpload, id=video_id, created_by=request.user)  # Retrieving video object
    video.public = not video.public  # Toggling video visibility
    video.save()  

    if video.public:
        # Copying private ratings to public ratings for the same video and user
        private_ratings = Rating.objects.filter(video=video, user=request.user, is_public=False)
        for private_rating in private_ratings:
            public_rating, created = Rating.objects.get_or_create(
                video=video,
                user=request.user,
                is_public=True,
                defaults={
                    'facial_inconsistencies': private_rating.facial_inconsistencies,
                    'glitches_or_artifacts': private_rating.glitches_or_artifacts,
                    'background_quality': private_rating.background_quality,
                    'lip_sync_accuracy': private_rating.lip_sync_accuracy,
                    'overall_score': private_rating.overall_score,
                }
            )
            if not created:
                # Updating existing public ratings if already created
                public_rating.facial_inconsistencies = private_rating.facial_inconsistencies
                public_rating.glitches_or_artifacts = private_rating.glitches_or_artifacts
                public_rating.background_quality = private_rating.background_quality
                public_rating.lip_sync_accuracy = private_rating.lip_sync_accuracy
                public_rating.overall_score = private_rating.overall_score
                public_rating.save()

    return redirect('core:index')   


@login_required  
def delete_video(request, video_id):
    video = get_object_or_404(MediaUpload, id=video_id, created_by=request.user)  
    if request.method == 'POST':  
        video.delete()  
        return redirect('core:index')  
    return render(request, 'core/confirm_delete.html', {'video': video}) 


@login_required  
def public_videos(request):
    # Querying public videos and calculating average ratings
    public_videos = MediaUpload.objects.filter(public=True).annotate(
        avg_facial_inconsistencies=Avg('ratings__facial_inconsistencies', filter=Q(ratings__is_public=True)),
        avg_glitches_or_artifacts=Avg('ratings__glitches_or_artifacts', filter=Q(ratings__is_public=True)),
        avg_background_quality=Avg('ratings__background_quality', filter=Q(ratings__is_public=True)),
        avg_lip_sync_accuracy=Avg('ratings__lip_sync_accuracy', filter=Q(ratings__is_public=True)),
        avg_overall_score=Avg(
            (F('ratings__facial_inconsistencies') + F('ratings__glitches_or_artifacts') +
             F('ratings__background_quality') + F('ratings__lip_sync_accuracy')) / 4,
            filter=Q(ratings__is_public=True)
        )
    )
    return render(request, 'core/public_videos.html', {
        'public_videos': public_videos,  
    })


@login_required  
def index(request):
    if not request.user.is_authenticated:  
        return redirect('core:login')

    form = MediaUploadForm()  # Creating a blank form for GET requests
    user_videos = MediaUpload.objects.filter(created_by=request.user)  # Querying user's uploaded videos

    # Annotating user's videos with private ratings
    annotated_videos = user_videos.annotate(
        private_avg_score=Avg('ratings__overall_score', filter=Q(ratings__user=request.user, ratings__is_public=False)),
        user_facial_inconsistencies=Avg('ratings__facial_inconsistencies', filter=Q(ratings__user=request.user, ratings__is_public=False)),
        user_glitches_or_artifacts=Avg('ratings__glitches_or_artifacts', filter=Q(ratings__user=request.user, ratings__is_public=False)),
        user_background_quality=Avg('ratings__background_quality', filter=Q(ratings__user=request.user, ratings__is_public=False)),
        user_lip_sync_accuracy=Avg('ratings__lip_sync_accuracy', filter=Q(ratings__user=request.user, ratings__is_public=False))
    )

    all_videos = [video for video in annotated_videos if video.video.name]  # Filtering out videos without names

    return render(request, 'core/index.html', {
        'form': form,  
        'all_videos': all_videos,  
    })


@login_required 
def rate_private_video(request, video_id):
    video = get_object_or_404(MediaUpload, id=video_id, created_by=request.user) 
    
    rating, created = Rating.objects.get_or_create(video=video, user=request.user, is_public=False)  

    if request.method == 'POST':  
        form = RatingForm(request.POST, instance=rating) 
        if form.is_valid(): 
            rating = form.save(commit=False)  # Saving form data to rating object without committing to DB

            # Calculating overall score from individual ratings
            rating.overall_score = (
                rating.facial_inconsistencies + 
                rating.glitches_or_artifacts + 
                rating.background_quality + 
                rating.lip_sync_accuracy
            ) / 4

            rating.user = request.user  # Setting rating user
            rating.video = video  # Setting rating video
            rating.is_public = False  # Setting rating visibility

            rating.save()  
            return redirect('core:index')  
        else:
            print(form.errors)  
    else:
        form = RatingForm(instance=rating)  

    return render(request, 'core/rate_private_video.html', {
        'form': form,  
        'video': video 
    })


@login_required  
def rate_public_video(request, video_id):
    video = get_object_or_404(MediaUpload, id=video_id, public=True) 
    
    rating, created = Rating.objects.get_or_create(video=video, user=request.user, is_public=True)  

    if request.method == 'POST':  
        form = RatingForm(request.POST, instance=rating)  
        if form.is_valid(): 
            rating = form.save(commit=False)  

            # Calculating overall score from individual ratings
            rating.overall_score = (
                rating.facial_inconsistencies + 
                rating.glitches_or_artifacts + 
                rating.background_quality + 
                rating.lip_sync_accuracy
            ) / 4

            rating.user = request.user  # Setting rating user
            rating.video = video  # Setting rating video
            rating.is_public = True  # Setting rating visibility

            rating.save()   
            return redirect('core:public_videos')   
        else:
            print(form.errors)  
    else:
        form = RatingForm(instance=rating)  

    return render(request, 'core/rate_public_video.html', {
        'form': form,   
        'video': video   
    })


def signup(request):
    if request.method == 'POST':   
        form = SignupForm(request.POST)   
        if form.is_valid():   
            user = form.save(commit=False)  # Saving form data to user object without committing to DB

            user.email = form.cleaned_data['email'].lower()  # Cleaning and setting email
            user.username = form.cleaned_data['username'].lower()  # Cleaning and setting username

            user.save()   
            login(request, user)  # Logging in user
            return redirect('core:index')   
    else:
        form = SignupForm()  

    return render(request, 'core/signup.html', {
        'form': form,   
    })


def logout_view(request):
    logout(request)  # Logging out user
    return redirect('/login/')   
