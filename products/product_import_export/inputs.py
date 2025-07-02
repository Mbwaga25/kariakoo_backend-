import graphene

class ImportInput(graphene.InputObjectType):
    file_type = graphene.String(required=True)
    file_content = graphene.String(required=True)
    file = graphene.String(required=False)
    import_type = graphene.String(required=True)
    update_existing = graphene.Boolean(default=False)
    create_related = graphene.Boolean(default=True, description="Create related models if they don't exist")

class ExportInput(graphene.InputObjectType):
    export_type = graphene.String(required=True)
    format = graphene.String(required=True)
    filters = graphene.JSONString(description="Optional filters for the export")