import graphene
from ..models import FoodVendor
from ..types.food import FoodVendorType
from ..inputs.food import RegisterFoodVendorInput

class RegisterFoodVendor(graphene.Mutation):
    class Arguments:
        input = RegisterFoodVendorInput(required=True)

    Output = FoodVendorType

    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required")

        food_vendor = FoodVendor.objects.create(
            user=user,
            business_name=input.business_name,
            cuisine_type=input.cuisine_type,
            location=input.location,
            phone=input.phone,
        )
        return food_vendor
