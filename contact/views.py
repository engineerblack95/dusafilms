from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm


def contact_view(request):
    """
    Contact page logic:
    - Authenticated users: name & email auto-filled and locked by logic
    - Guests: manual input
    - On success: save message + show success alert
    """

    if request.method == "POST":
        form = ContactForm(request.POST)

        if form.is_valid():
            contact = form.save(commit=False)

            # Attach user data if logged in
            if request.user.is_authenticated:
                contact.user = request.user
                contact.name = request.user.username
                contact.email = request.user.email

            contact.save()

            # Success feedback
            messages.success(
                request,
                "✅ Your message has been sent successfully. We’ll contact you shortly."
            )

            return redirect("contact:contact")

    else:
        # Pre-fill form for authenticated users
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                "name": request.user.username,
                "email": request.user.email,
            }

        form = ContactForm(initial=initial_data)

    return render(request, "contact/contact.html", {
        "form": form
    })
