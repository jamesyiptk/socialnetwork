from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from socialnetwork.forms import LoginForm, RegisterForm, ProfileForm
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, Http404
from django.conf import settings

from socialnetwork.models import Post, Profile, Comment
import os
import json


def login_action(request):
    context = {}

    # Just display the registration form if this is a GET request.
    if request.method == 'GET':
        context['form'] = LoginForm()
        return render(request, 'socialnetwork/login.html', context)

    # Creates a bound form from the request POST parameters and makes the
    # form available in the request context dictionary.
    form = LoginForm(request.POST)
    context['form'] = form

    # Validates the form.
    if not form.is_valid():
        return render(request, 'socialnetwork/login.html', context)

    new_user = authenticate(username=form.cleaned_data['username'],
                            password=form.cleaned_data['password'])

    login(request, new_user)
    return redirect(reverse('home'))


def logout_action(request):
    logout(request)
    return redirect(reverse('login'))


def register_action(request):
    context = {}

    # Just display the registration form if this is a GET request.
    if request.method == 'GET':
        context['form'] = RegisterForm()
        return render(request, 'socialnetwork/register.html', context)

    # Creates a bound form from the request POST parameters and makes the
    # form available in the request context dictionary.
    form = RegisterForm(request.POST)
    context['form'] = form

    # Validates the form.
    if not form.is_valid():
        return render(request, 'socialnetwork/register.html', context)

    # At this point, the form data is valid.  Register and login the user.
    new_user = User.objects.create_user(username=form.cleaned_data['username'],
                                        password=form.cleaned_data['password'],
                                        email=form.cleaned_data['email'],
                                        first_name=form.cleaned_data['first_name'],
                                        last_name=form.cleaned_data['last_name'])
    new_user.save()

    # Create a Profile for the new user
    Profile.objects.create(user=new_user)  # This line creates a profile for each new user

    new_user = authenticate(username=form.cleaned_data['username'],
                            password=form.cleaned_data['password'])

    if new_user is not None:
        login(request, new_user)
    return redirect(reverse('home'))


@login_required
@ensure_csrf_cookie
def global_stream(request):
    return render(request, 'socialnetwork/global_stream.html', {'posts': Post.objects.all().order_by('-creation_time')})


def get_global(request):
    if not request.user.is_authenticated:
        response_data = {"error": "You must be logged in to do this operation"}
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)

    # It first selects all the posts and order it by creation_time,
    # then fetch the related comments for each of those posts
    posts = Post.objects.all().order_by('-creation_time').prefetch_related('comment_set')

    response_data = {
        'posts': [],
        'comments': []
    }

    # Serialize the posts
    for post in posts:
        post_data = {
            'id': post.id,
            'text': post.text,
            'user': {
                'username': post.user.get_full_name(),
                'id': post.user.id
            },
            'creation_time': timezone.localtime(post.creation_time).isoformat()
        }
        response_data['posts'].append(post_data)

        # Serialize the comments for each post
        for comment in post.comment_set.all():
            comment_data = {
                'id': comment.id,
                'text': comment.text,
                'creator': {
                    'username': comment.creator.get_full_name(),
                    'id': comment.creator.id
                },
                'creation_time': timezone.localtime(comment.creation_time).isoformat(),
                'post_id': post.id
            }
            response_data['comments'].append(comment_data)

    # Convert the response data to JSON
    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type='application/json')


def get_follower(request):
    if not request.user.is_authenticated:
        response_data = {"error": "You must be logged in to do this operation"}
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)

    # Get the list of users that the current user is following
    following_users = request.user.profile.following.all()

    # Filter posts to only include those whose user is in 'following_users'
    posts = Post.objects.filter(user__in=following_users).exclude(user=request.user).order_by('-creation_time').prefetch_related('comment_set')

    response_data = {
        'posts': [],
        'comments': []
    }

    # Serialize the posts
    for post in posts:
        post_data = {
            'id': post.id,
            'text': post.text,
            'user': {
                'username': post.user.get_full_name(),
                'id': post.user.id
            },
            'creation_time': timezone.localtime(post.creation_time).isoformat()
        }
        response_data['posts'].append(post_data)

        # Serialize the comments for each post
        for comment in post.comment_set.all():
            comment_data = {
                'id': comment.id,
                'text': comment.text,
                'creator': {
                    'username': comment.creator.get_full_name(),
                    'id': comment.creator.id
                },
                'creation_time': timezone.localtime(comment.creation_time).isoformat(),
                'post_id': post.id
            }
            response_data['comments'].append(comment_data)

    # Convert the response data to JSON
    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type='application/json')


def add_post(request):
    if not request.user.is_authenticated:
        response_data = {"error": "You must be logged in to do this operation"}
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)

    if request.method == 'POST':
        post_text = request.POST['post_text']  # post_text is the name of the input field in global_stream.html
        if not post_text:
            response_data = {"error": "You must enter some text to add a new post."}
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

        new_post = Post(text=post_text, user=request.user, creation_time=timezone.now())
        new_post.save()

        return get_global(request)
    else:
        response_data = {"error": "You must use a POST request for this operation"}
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=405)


@require_POST
def add_comment(request):
    if not request.user.is_authenticated:
        response_data = {"error": "You must be logged in to do this operation"}
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)

    post_id = request.POST.get('post_id')

    if not post_id:
        response_data = {"error": "You must specify a post to comment on."}
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

    if not post_id.isdigit():
        response_data = {"error": "You must specify a post to comment on."}
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

    comment_text = request.POST.get('comment_text')
    if not post_id or not comment_text:
        response_data = {"error": "You must enter a comment and specify a post."}
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

    try:
        post_id = int(post_id)
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        response_data = {"error": "Post not found."}
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

    new_comment = Comment(text=comment_text, creation_time=timezone.now(), creator=request.user, post=post)
    new_comment.save()

    # After creating the new comment, decide which stream's data to return
    if 'return_to_follower_stream' in request.POST and request.POST['return_to_follower_stream'] == 'true':
        return get_follower(request)
    else:
        return get_global(request)


@login_required
def follower_stream_action(request):
    if request.method == "GET":
        posts = Post.objects.filter(user__in=request.user.profile.following.all()).order_by('-creation_time')
        return render(request, 'socialnetwork/follower_stream.html', {'posts': posts})


@login_required
def my_profile_action(request):
    # Attempt to get the user's profile, or create a new one if it does not exist
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        form = ProfileForm(instance=profile)  # Populate form with profile instance
        return render(request, "socialnetwork/profile.html", {'profile_form': form})

    # Handling POST request
    form = ProfileForm(request.POST, request.FILES, instance=profile)
    if form.is_valid():
        # Before saving the form, grab the content_type and assign it
        profile = form.save(commit=False)
        if 'picture' in request.FILES:
            profile.content_type = form.cleaned_data['picture'].content_type
        profile.save()
        return redirect('profile')  # Use the 'name' of the URL pattern for the profile page
    else:
        return render(request, "socialnetwork/profile.html", {'profile_form': form})


@login_required
def other_profile_action(request, id):
    other_user = get_object_or_404(User, id=id)
    # Try to retrieve the profile, or set it to None if it doesn't exist
    try:
        other_profile = other_user.profile
    except Profile.DoesNotExist:
        other_profile = None

    context = {
        'other_profile': other_profile,
        'other_user': other_user,  # Include the user in the context
    }
    return render(request, 'socialnetwork/other_profile.html', context)


@login_required
def unfollow_action(request, id):
    user_to_unfollow = get_object_or_404(User, id=id)
    request.user.profile.following.remove(user_to_unfollow)
    request.user.profile.save()

    # Redirect back to the user's profile page after unfollowing.
    return redirect('other_profile', id=id)


@login_required
def follow_action(request, id):
    user_to_follow = get_object_or_404(User, pk=id)
    # Ensure the requesting user has a profile
    profile, created = Profile.objects.get_or_create(user=request.user)
    # Add the user to follow to the following list
    profile.following.add(user_to_follow)

    # Redirect to the user's profile page after following.
    return redirect('other_profile', id=id)


@login_required
def get_photo(request, id):
    profile = get_object_or_404(Profile, id=id)

    if not profile.picture:
        raise Http404('No image found.')

    # Set the content type of the response to the file's content type
    content_type = profile.content_type
    # Open the file for reading in binary mode
    file_path = os.path.join(settings.MEDIA_ROOT, profile.picture.name)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            return HttpResponse(file.read(), content_type=content_type)
    else:
        raise Http404('Image not found.')
