from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from appointments.models import Service
from appointments.forms import ServiceForm


def service_list_view(request):
    services = Service.objects.all()
    return render(request, 'appointments/service_list.html', {'services': services})


@staff_member_required
def service_detail_view(request, service_id):
    service = get_object_or_404(Service, id=service_id)

    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            service = form.save()
            messages.success(request, f"Serviço {service.name} alterado com sucesso.")
            return redirect('service_list')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'appointments/owner_service_detail.html', {'form': form, 'service': service})
