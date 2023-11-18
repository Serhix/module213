from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404

from .forms import TagForm, AuthorForm, QuoteForm
from .models import Tag, Author, Quote
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from . import scraper


# Create your views here.


def main(request):
    quotes = Quote.objects.all()
    paginator = Paginator(quotes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    tags = Tag.objects.all()
    tag_counts = Tag.objects.annotate(quote_count=Count('quote')).order_by('-quote_count')[:10]
    return render(request, 'quoteapp/index.html', {'page_obj': page_obj, "quotes": quotes, "tag": tags, 'author': author, 'top_tags': tag_counts})


@login_required
def tag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(to='quoteapp:main')
        else:
            return render(request, 'quoteapp/tag.html', {'form': form})

    return render(request, 'quoteapp/tag.html', {'form': TagForm()})


@login_required
def author(request):
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(to='quoteapp:main')
        else:
            return render(request, 'quoteapp/author.html', {'form': form})

    return render(request, 'quoteapp/author.html', {'form': AuthorForm()})


@login_required
def quote(request):
    tags = Tag.objects.all()
    authors = Author.objects.all()

    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            new_quote = form.save(commit=False)  # Зберігаємо форму без збереження в базу даних
            new_quote.autor = Author.objects.get(fullname=request.POST['author'])
            new_quote.save()
            choice_tags = Tag.objects.filter(name__in=request.POST.getlist('tags'))
            for tag in choice_tags.iterator():
                new_quote.tags.add(tag)

            return redirect(to='quoteapp:main')
        else:
            return render(request, 'quoteapp/quote.html', {"tags": tags, 'author': authors, 'form': form})

    return render(request, 'quoteapp/quote.html', {"tags": tags, 'author': authors, 'form': QuoteForm()})


@login_required
def start_scraping(request):
    if request.method == 'POST':
        scraper.main()
    return render(request, 'quoteapp/scraper.html')


def about_author(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    return render(request, 'quoteapp/about.html', {'author': author})


def quotes_by_tag(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    quotes = Quote.objects.filter(tags=tag)
    authors = Author.objects.all()
    tag_counts = Tag.objects.annotate(quote_count=Count('quote')).order_by('-quote_count')[:10]
    return render(request, 'quoteapp/quotes_by_tag.html', {"quotes": quotes, "tag": tag, 'author': authors, 'top_tags': tag_counts})

