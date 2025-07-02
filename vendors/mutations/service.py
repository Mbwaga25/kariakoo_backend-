import graphene
from ..models import ServiceProvider
from ..types.service import ServiceProviderType
from ..inputs.service import RegisterServiceProviderInput

class RegisterServiceProvider(graphene.Mutation):
    class Arguments:
        input = RegisterServiceProviderInput(required=True)
    Output = ServiceProviderType

    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")

        service_provider = ServiceProvider.objects.create(
            user=user,
            service_name=input.service_name,
            description=input.description,
            phone=input.phone,
            location=input.location,
        )
        return service_provider
