from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt
from subscription.models import Package, Subscription
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from subscription import serializers

stripe.api_key = settings.STRIPE_SECRET_KEY

class SubscriptionViewSet(ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = serializers.SubscriptionSerializer
    permission_classes = [IsAdminUser]


    @action(detail=False, methods=['GET'],permission_classes=[IsAuthenticated])
    def me(self, request):
        subscriptions = Subscription.objects.filter(user=self.request.user)
        if request.method == 'GET':
            serializer = serializers.SubscriptionSerializer(subscriptions, many=True)
            return Response(serializer.data)

class PackageViewset(ReadOnlyModelViewSet):
    queryset = Package.objects.all()
    serializer_class = serializers.PackageSerializer
    permission_classes = [AllowAny]
# Create your views here.
class CreateCheckoutSessionView(APIView):
    def post(self, request, *args, **kwargs):
        package = Package.objects.get(id=request.data['packID'])
        YOUR_DOMAIN = "http://127.0.0.1:8000"            
        if Subscription.objects.filter(user_id=request.user.id, package_id=request.data['packID'], active=True).exists():
            return Response({
                'code' : 'subscribed_already',
                'msg': 'you have already active subscription with this package'
            }, status=400)
        else:
            metadataData = {}
            if request.data.get('subType') == 'extension' and request.data.get('subID'):
                if Subscription.objects.filter(id=request.data.get('subID'), user=request.user.id).exists():
                    metadataData = {
                        "duration": request.data['duration'],
                        "package_id" : request.data['packID'],
                        "user" : request.user.id,
                        "subType": request.data.get('subType'),
                        "subID" : request.data.get('subID')
                    }
                else:
                    return Response({
                        'code' : 'subscription_not_exit',
                        'msg': "you don't have subscription with this id"
                    }, status=404)

            else:
                metadataData = {
                    "duration": request.data['duration'],
                    "package_id" : request.data['packID'],
                    "user" : request.user.id,
                }
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'gbp',
                            'unit_amount': request.data['price'] * 100,
                            'product_data': {
                                'name': package.title,
                                'description' : str(request.data['duration']) + ' months subscription',                                
                            },
                        },
                        'quantity': 1,
                    },
                ],
                metadata=metadataData,
                mode='payment',
                allow_promotion_codes=True,
                success_url=settings.STRIPE_SUCCESS_REDIRECT_URL,
                cancel_url=settings.STRIPE_CANCEL_REDIRECT_URL
            )
            return Response({
                'id': checkout_session.id
            })

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':

        session = event['data']['object']

        print(session.metadata.get('subType'), session.metadata.get('subID'))

        if session.metadata.get('subType') == 'extension' and session.metadata.get('subID'): 
            try:
                print('extend')
                subscription = Subscription.objects.get(id=session.metadata.get('subID'))
                subscription.set_expiry_date(int(session.metadata['duration']))
                subscription.active = True
                subscription.save()
            except Subscription.DoesNotExist:
                return HttpResponse(status=404)       
        else:
            print('extendG')
            subscription = Subscription(user_id=session.metadata['user'], package_id=session.metadata['package_id'])
            subscription.set_expiry_date(int(session.metadata['duration']))
            subscription.save()

    return HttpResponse(status=200)

