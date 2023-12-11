import json

import rest_framework
from django.db.models import Q, F
from django.utils import timezone

from django.shortcuts import render
from rest_framework import status, serializers
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model

# Create your views here.
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView

from seminar.models import Seminar, UserSeminar
from seminar.serializers import SeminarSerializer, SeminarViewSerializer, RegisterSeminarService, DropSeminarService
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from survey.models import SurveyResult


class SeminarViewSet(GenericViewSet):
    serializer_class = SeminarSerializer
    queryset = Seminar.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter,)
    filter_fields = ('name',)
    ordering_fields = ('created_at',)

    def list(self, request):
        serializer = SeminarViewSerializer
        return Response(serializer(self.queryset, many=True).data)

    def retrieve(self, request, pk=None):

        try:
            seminar = Seminar.objects.get(id=pk)
        except Seminar.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data='그런 세미나는 없습니다')

        return Response(self.get_serializer(seminar).data)

    def create(self, request):

        data = request.data

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        seminar = serializer.save()

        return Response(self.get_serializer(seminar).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):

        # Fixme: 위의 retrieve 에서 같은 404 처리를 어떻게 하는지 함께 비교해보시면 될 듯 합니다. 많은 경우에 get() 호출 시 에러가 아닌 다른 처리를 해주어야 합니다.
        #  이 때 BaseManager 를 상속 후 함수를 추가하고, 이를 매니저로 사용하는 모델을 커스텀함으로써 모든 모델에 손쉽게 해당 로직을 반영할 수 있습니다.
        #  이런 식의 구현에서 좀 더 나아가면, 상황별로 exception 을 custom 하고, 직접 exception_handler 를 구현 뒤 등록할 수도 있습니다.

        if not (seminar := Seminar.objects.get_or_none(id=pk)):
            return Response(status=status.HTTP_404_NOT_FOUND, data='그런 세미나는 없습니다.')

        serializer = self.get_serializer(data=request.data, context={'request': request}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(seminar, serializer.validated_data)

        return Response(self.get_serializer(seminar).data, status=status.HTTP_200_OK)


class UserSeminarView(APIView):

    def delete(self, request, seminar_id=None):

        service = DropSeminarService(
            data={'role': request.data.get('role')},
            context={'request': request, 'seminar_id': seminar_id}
        )
        status_code, data = service.execute()

        return Response(status=status_code, data=data)

    def post(self, request, seminar_id=None):

        service = RegisterSeminarService(
            data={'role': request.data.get('role')},
            context={'request': request, 'seminar_id': seminar_id}
        )
        status_code, data = service.execute()

        return Response(status=status_code, data=data)


@api_view(['GET'])
def query_practice(request):

    survey = SurveyResult.objects.filter(
        rdb__gt=F('python')
    ).count()

    return Response(data=survey)
