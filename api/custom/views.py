from rest_framework import viewsets


class CustomBaseModelViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.filter(
            created_by=self.kwargs["user_id"],
        )


class CustomBaseModelViewSetUser(viewsets.ModelViewSet):
    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.filter(
            workspace__created_by=self.kwargs["user_id"],
        )
