from rest_framework.renderers import JSONRenderer

class EnvelopeJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None
        status_code = getattr(response, "status_code", 200)
        if status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)
        if isinstance(data, dict) and "results" in data and "count" in data:
            return super().render({"success": True, "data": data}, accepted_media_type, renderer_context)
        if isinstance(data, dict) and data.get("success") in (True, False):
            return super().render(data, accepted_media_type, renderer_context)
        return super().render({"success": True, "data": data}, accepted_media_type, renderer_context)