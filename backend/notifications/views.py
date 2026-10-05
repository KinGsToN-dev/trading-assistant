from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import NotificationSettings, NotificationLog
from .serializers import NotificationSettingsSerializer, NotificationLogSerializer
from .services.telegram import send_message, send_to_user


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def settings_view(request):
    """Получить или обновить настройки уведомлений."""
    obj, _ = NotificationSettings.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        return Response(NotificationSettingsSerializer(obj).data)

    # PATCH
    serializer = NotificationSettingsSerializer(obj, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_telegram(request):
    """
    Привязать Telegram chat_id к пользователю.
    Body: {"chat_id": "123456789"}
    """
    chat_id = str(request.data.get('chat_id', '')).strip()
    if not chat_id:
        return Response(
            {'detail': 'chat_id обязателен'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Отправляем тестовое сообщение — проверяем, что chat_id валиден
    result = send_message(chat_id, '✅ Telegram успешно привязан к Trading Assistant!')
    if not result['ok']:
        return Response(
            {'detail': f'Telegram отказал: {result.get("error")}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    obj, _ = NotificationSettings.objects.get_or_create(user=request.user)
    obj.telegram_chat_id = chat_id
    obj.telegram_linked_at = timezone.now()
    obj.save()

    # Также сохраняем в User (на случай, если используется старое поле)
    request.user.telegram_chat_id = chat_id
    request.user.save(update_fields=['telegram_chat_id'])

    return Response({'detail': 'Telegram привязан', 'chat_id': chat_id})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlink_telegram(request):
    """Отвязать Telegram."""
    obj, _ = NotificationSettings.objects.get_or_create(user=request.user)
    obj.telegram_chat_id = ''
    obj.telegram_linked_at = None
    obj.save()

    request.user.telegram_chat_id = ''
    request.user.save(update_fields=['telegram_chat_id'])

    return Response({'detail': 'Telegram отвязан'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_notification(request):
    """Отправить тестовое уведомление."""
    ok = send_to_user(
        request.user,
        '🔔 <b>Тестовое уведомление</b>\n\nВсё работает! Уведомления будут приходить сюда.',
        kind='test',
    )
    if ok:
        return Response({'detail': 'Уведомление отправлено'})
    return Response(
        {'detail': 'Telegram не привязан или произошла ошибка'},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def history(request):
    """Последние 50 уведомлений."""
    logs = NotificationLog.objects.filter(user=request.user)[:50]
    return Response(NotificationLogSerializer(logs, many=True).data)