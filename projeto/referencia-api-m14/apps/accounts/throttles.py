from rest_framework_simplejwt.views import TokenObtainPairView

from config.throttling import LoginThrottleFechado


class ThrottledTokenView(TokenObtainPairView):
    throttle_classes = [LoginThrottleFechado]  # falha FECHADA se o cache cair (config/throttling.py)
    throttle_scope = "login"  # taxa própria, bem mais baixa que a geral
