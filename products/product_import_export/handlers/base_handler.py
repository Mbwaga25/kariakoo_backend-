# your_app/graphql/handlers/base_handler.py
class BaseHandler:
    model = None
    required_fields = []
    lookup_field = 'name'  # Default primary field for lookup, can be overridden

    def __init__(self, update_existing=False, create_related=True):
        """
        Initializes the handler.
        - update_existing: If True, existing records will be updated.
        - create_related: If True, new records (and their sub-relations if applicable) can be created.
        """
        self.update_existing = update_existing
        self.create_related = create_related # This is key for controlling creation behavior

    def validate_data(self, data, current_errors):
        """
        Validates the input data against required_fields.
        Appends errors to the provided current_errors list.
        Returns True if data is valid, False otherwise.
        """
        is_valid = True
        for field in self.required_fields:
            if not data.get(field):
                current_errors.append(f"Field '{field}' is required for {self.model.__name__ if self.model else 'this entity'}.")
                is_valid = False
        return is_valid

    def handle(self, data):
        """
        Main method to process data for an entity.
        Each subclass must implement this.
        Should return a dictionary:
        {
            'instance': Django model instance or None,
            'status': 'created', 'updated', 'skipped', 'error', or 'completed_with_errors',
            'errors': list of error message strings
        }
        """
        raise NotImplementedError("Each handler must implement the 'handle' method.")

    def _get_lookup_params(self, data):
        """Helper to extract lookup parameters based on self.lookup_field or a list of fields."""
        params = {}
        if isinstance(self.lookup_field, str):
            if data.get(self.lookup_field):
                params[self.lookup_field] = data.get(self.lookup_field)
            else:
                return None, [f"Lookup field '{self.lookup_field}' not found in data."]
        elif isinstance(self.lookup_field, (list, tuple)):
            for field in self.lookup_field:
                if data.get(field):
                    params[field] = data.get(field)
                else:
                    return None, [f"Lookup field '{field}' not found in data."]
            if not params: # Ensure at least one lookup field was found
                 return None, [f"None of the lookup fields {self.lookup_field} found in data."]
        else:
            return None, ["Invalid lookup_field configuration in handler."]
        return params, []