import json
import os
import tempfile

from django.http import JsonResponse
from django.shortcuts import render

from apps.meetings.services.audio_processing import AudioProcessingError, process_audio
from apps.meetings.services.meeting_pipeline import process_meeting

SAMPLE_TRANSCRIPT = [
    {
        "speaker": "speaker_5",
        "timestamp": "00:12:10",
        "text": "I'll prepare the report by Monday.",
    },
    {
        "speaker": "speaker_2",
        "timestamp": "00:13:02",
        "text": "I will test the login module before the release review.",
    },
    {
        "speaker": "speaker_5",
        "timestamp": "00:18:40",
        "text": "The client approved the revised rollout timeline.",
    },
]


def _process_meeting_submission(request):
    """Process transcript or uploaded audio input and return UI-friendly state."""
    transcript_input = request.POST.get("transcript", "").strip()
    uploaded_file = request.FILES.get("meeting_file")
    result = None
    error_message = ""

    try:
        transcript = []

        if uploaded_file:
            file_name = uploaded_file.name.lower()

            if file_name.endswith(".txt"):
                file_text = uploaded_file.read().decode("utf-8").strip()
                transcript_input = file_text or transcript_input
                transcript = json.loads(file_text or "[]")
            elif file_name.endswith(".mp3"):
                suffix = os.path.splitext(uploaded_file.name)[1] or ".mp3"
                temp_file_path = ""

                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=suffix
                    ) as temp_file:
                        for chunk in uploaded_file.chunks():
                            temp_file.write(chunk)
                        temp_file_path = temp_file.name

                    transcript = process_audio(
                        temp_file_path,
                        upload_name=uploaded_file.name,
                    )
                    transcript_input = json.dumps(transcript, indent=2)
                finally:
                    if temp_file_path and os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
            else:
                raise ValueError("Unsupported file type. Use a .txt or .mp3 file.")
        elif transcript_input:
            transcript = json.loads(transcript_input)
        else:
            raise ValueError(
                "Provide either transcript JSON or upload a supported file."
            )

        if not isinstance(transcript, list):
            raise ValueError("Transcript must be a JSON array of entries.")

        result = process_meeting(transcript)
    except json.JSONDecodeError:
        error_message = "Transcript must be valid JSON."
    except AudioProcessingError as exc:
        error_message = str(exc)
    except ValueError as exc:
        error_message = str(exc)
    except Exception:
        error_message = "Meeting processing failed. Check the transcript format and AI configuration."

    return {
        "transcript_input": transcript_input,
        "result": result,
        "error_message": error_message,
    }


def meeting_list(request):
    """Render the meetings workspace and process transcript submissions."""
    transcript_input = json.dumps(SAMPLE_TRANSCRIPT, indent=2)
    result = None
    error_message = ""

    if request.method == "POST":
        submission_state = _process_meeting_submission(request)
        transcript_input = submission_state["transcript_input"] or transcript_input
        result = submission_state["result"]
        error_message = submission_state["error_message"]

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "ok": not bool(error_message),
                    "transcript_input": transcript_input,
                    "result": result,
                    "error_message": error_message,
                }
            )

    context = {
        "transcript_input": transcript_input,
        "result": result,
        "error_message": error_message,
        "sample_transcript": json.dumps(SAMPLE_TRANSCRIPT, indent=2),
    }
    return render(request, "meetings/list.html", context)
