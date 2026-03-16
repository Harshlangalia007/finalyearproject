from django.shortcuts import render

def meeting_list(request):
    # Return list of meetings
    return render(request, 'meetings/list.html')
