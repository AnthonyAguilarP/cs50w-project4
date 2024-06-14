from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
import json
from django.http import JsonResponse
from .models import User, Post, Follow, Like

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

def add_like(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=post_id)
        user = request.user
        like, created = Like.objects.get_or_create(user=user, post=post)
        if created:
            return JsonResponse({"message": "Like added"})
        else:
            return JsonResponse({"message": "Like already exists"})

def remove_like(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=post_id)
        user = request.user
        like = Like.objects.filter(user=user, post=post).first()
        if like:
            like.delete()
            return JsonResponse({"message": "Like removed"})
        else:
            return JsonResponse({"message": "Like does not exist"})


def edit(request, post_id):
    if request.method == 'POST':
        data=json.loads(request.body)
        editPost=Post.objects.get(pk=post_id)
        editPost.content=data["content"]
        editPost.save()
        return JsonResponse({"message": "change successful",
                             "data": data["content"],})

def following(request):
    currentUser = User.objects.get(pk=request.user.id)
    followingPeople = Follow.objects.filter(user=currentUser)
    allPosts=Post.objects.all().order_by('id').reverse()
    followingPosts=[]
    for post in allPosts:
        for person in followingPeople:
            if person.user_follower==post.author:
                followingPosts.append(post)
                
    paginator=Paginator(followingPosts, 10)
    pageNumber=request.GET.get('page')
    postPage=paginator.get_page(pageNumber)
    return render(request, "network/following.html", {
        "postPage": postPage,
    })
    

def index(request):
    allPosts = Post.objects.all().order_by("id").reverse()
    
    paginator=Paginator(allPosts, 10)
    pageNumber=request.GET.get('page')
    postPage=paginator.get_page(pageNumber)
    
    allLikes=Like.objects.all()
    whoYouLiked=[]
    try:
        for like in allLikes:
            whoYouLiked.append(like.post.id)
    except:
        whoYouLiked=[]
    
    
    return render(request, "network/index.html",{
        "allPosts": allPosts,
        "postPage": postPage,
        "whoYouLiked": whoYouLiked
    })


def newPost(request):
    if request.method == 'POST':
        content=request.POST['content']
        user=User.objects.get(pk=request.user.id)
        post = Post(content=content, author=user)
        post.save()
        return HttpResponseRedirect(reverse(index))

def profile(request, user_id):
    user=User.objects.get(pk=user_id)
    allPosts = Post.objects.filter(author=user).order_by("id").reverse()
    following=Follow.objects.filter(user=user)
    followers=Follow.objects.filter(user_follower=user)
    try:
        checkFollow=followers.filter(user=User.objects.get(pk=request.user.id))
        if len(checkFollow) != 0:
            isFollowing=True
        else:
            isFollowing=False
    except:
        isFollowing = False
    
    paginator=Paginator(allPosts, 10)
    pageNumber=request.GET.get('page')
    postPage=paginator.get_page(pageNumber)
    
    
    return render(request, "network/profile.html",{
        "allPosts": allPosts,
        "postPage": postPage,
        "username": user.username,
        "followers": followers,
        "following": following,
        "isFollowing": isFollowing,
        "userProfile": user
    })
    
def unfollow(request):
    follow=request.POST['follow']
    currentUser=User.objects.get(pk=request.user.id)
    followData=User.objects.get(username=follow)
    f=Follow.objects.get(user=currentUser,user_follower=followData)
    f.delete()
    userId=followData.id
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': userId}))

def follow(request):
    follow=request.POST['follow']
    currentUser=User.objects.get(pk=request.user.id)
    followData=User.objects.get(username=follow)
    f=Follow(user=currentUser,user_follower=followData)
    f.save()
    userId=followData.id
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': userId}))

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
